import wave as wav
from typing import TextIO
from textwrap import TextWrapper
from sys import exit

import click
import numpy as np
import pyaudio
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.console import Console
from loguru import logger
from pyaudio import PyAudio

logger.remove()
logger.level("NOSHOW", 999, "black", "X")
console = Console()

import cwi.tone_generators as tone_generators
from cwi.const.log_fmt import CONSOLE_FORMAT
from cwi.const.service import PLAYBACK_BUFFER_SIZE, SAVING_BUFFER_SIZE
from cwi.const.service import MORSE_SAMPLER_TOKEN_CHUNK_SIZE
from cwi.data_structures import ToneGeneratorType, AudioData, Message
from cwi.converters import MorseTokenizer, TokenPurifier
from cwi.audio_sampler import MorseAudioSampler
from cwi.timer import Timer


class App:
    def __init__(self, tone_generator_type: str, frequency: float, sample_rate: int, words_per_minute: int):
        dit_duration = 1.2 / words_per_minute
        tone_generators_mapping = {
            ToneGeneratorType.SINE: tone_generators.SineWaveToneGenerator,
            ToneGeneratorType.SAW: tone_generators.SawtoothToneGenerator,
            ToneGeneratorType.TRIANGLE: tone_generators.TriangleToneGenerator,
            ToneGeneratorType.SQUARE: tone_generators.SquareToneGenerator,
        }

        try:
            tone_generator = tone_generators_mapping[tone_generator_type](frequency, sample_rate)
        except KeyError:
            logger.exception(f"Invalid tone generator type provided: {tone_generator_type}")
            raise ValueError(f"Invalid tone generator type provided: {tone_generator_type}")
        
        self.__frequency = frequency
        self.__sample_rate = sample_rate
        self.__dit_duration = dit_duration
        self.__wpm = words_per_minute
        self.__tone_generator_type = tone_generator_type
        
        try:
            self.__tokenizer = MorseTokenizer()
        except ValueError:
            logger.exception("Failed to initialize MorseTokenizer")
            logger.critical("Cannot proceed without tokenizer")
            exit(1)

        self.__audio_sampler = MorseAudioSampler(tone_generator, dit_duration)
        
        self.__message = Message()
        
        logger.debug(f"{self.__class__.__name__} initialized:")
        logger.info(f"{self.__class__.__name__} WPM: {words_per_minute}, dot duration: {dit_duration}s")
        logger.info(f"{self.__class__.__name__} Sample rate: {sample_rate}, frequency: {frequency}, tone: {tone_generator_type}")
        logger.debug(f"{self.__class__.__name__} {SAVING_BUFFER_SIZE=}, {PLAYBACK_BUFFER_SIZE}")
        logger.debug(f"{self.__class__.__name__} {MORSE_SAMPLER_TOKEN_CHUNK_SIZE=}")

    @property
    def dit_duration(self):
        return self.__dit_duration
    
    @property
    def message(self):
        return self.__message.actual
    
    @message.setter
    def message(self, val: str):
        token_string = self.__tokenizer.tokenize(val)
        
        self.__message.actual = val
        self.__message.morse_tokens = token_string
        self.__message.morse_readable = TokenPurifier.purify(token_string)
        
    @property
    def message_tokens(self):
        return self.__message.morse_tokens
    
    @property
    def message_morse_codes(self):
        return self.__message.morse_readable
    
    def generate_audio_data(self):
        return self.__audio_sampler.produce_audio_data(self.__message.morse_tokens, MORSE_SAMPLER_TOKEN_CHUNK_SIZE)
    
    def play_audio_data(self, audio_data: AudioData):
        audio_device = PyAudio()
        stream = audio_device.open(self.__sample_rate, 1, pyaudio.paFloat32, output=True)
        
        logger.debug(f"{audio_device.get_default_host_api_info()=}")
        logger.debug(f"{audio_device.get_default_output_device_info()=}")
        logger.debug(f"{stream.get_output_latency()=}")

        audio_data_f32 = audio_data.as_float32
        chunks = np.array_split(audio_data_f32, audio_data_f32.size / PLAYBACK_BUFFER_SIZE)
        progress = Progress("[green]|>", TimeElapsedColumn(), SpinnerColumn("point", finished_text="[gray50]___"), console=console)

        try:
            logger.info(f"Playing audio data...")
            with progress:
                task = progress.add_task("playing", total=len(chunks))
                for chunk in chunks:
                    stream.write(chunk.tobytes())
                    progress.update(task, advance=1)

        except Exception:
            logger.exception("PyAudio unknown Error")
            
        except KeyboardInterrupt:
            logger.info("Playback interrupted")
            
        else:
            logger.info("Playback completed successfully")
            
        finally:
            stream.close()
            audio_device.terminate()
            
            logger.debug(f"Stream closed, PyAudio device terminated")
            
    def save_audio_data(self, audio_data: AudioData, path: str):   
        try:
            logger.info(f"Writing audio data to {path=}...")
            with wav.open(path, "w") as wav_file:
                
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.__sample_rate)
                
                audio_data_i16 = audio_data.as_int16
                chunks = np.array_split(audio_data_i16, audio_data_i16.size / SAVING_BUFFER_SIZE)
                progress = Progress(f"[gray50]{path}",  MofNCompleteColumn(), SpinnerColumn("line", finished_text="[gray50]Complete"), console=console)

                with progress:
                    task = progress.add_task("saving", total=len(chunks))
                    for chunk in chunks:
                        wav_file.writeframes(chunk)
                        progress.advance(task, 1)
                        
        except OSError:
            logger.exception("Unexpected OS Exception")
            
        except KeyboardInterrupt:
            logger.info("Saving interrupted")
            
        else:
            logger.info("Saving completed successfully")
                    
    def print_app_info(self):
        console.print(f"WPM: {self.__wpm}")
        console.print(f"Dot duration: {self.__dit_duration}")
        console.print(f"Sample rate: {self.__sample_rate}")
        console.print(f"frequency: {self.__frequency}")
        console.print(f"Tone: [bold]{self.__tone_generator_type}[/]")
        
    def print_message_details(self): 
        wrapper = TextWrapper(console.width, 
                              initial_indent="[yellow blink]> [/][white]", 
                              subsequent_indent="[gray50]: [/][white]",
                              max_lines=4, placeholder="[gray50] <...>")
                   
        console.print(f"[bold]Original:",)
        console.print(wrapper.fill(self.message))
        console.line()
        console.print(f"[bold]Morse:")
        console.print(wrapper.fill(self.message_morse_codes))
            
    def print_unknown_characters(self):
        if self.message_tokens.unknown_entries:
            console.rule("Warning", style="bold yellow")
            console.line()
            console.print(f"Unknown characters found in message: [yellow]{' '.join(self.message_tokens.unknown_entries)}")
            console.line()
            console.rule("Warning", style="bold yellow")
            
    def print_no_input(self):
        console.rule("CRITICAL", style="bold red")
        console.line()
        console.print("[bold red]No input provided")
        console.line()
        console.rule("CRITICAL", style="bold red")


@click.command()
@click.argument("message", nargs=-1)
@click.option(
    "--tone-generator-type",
    "-t",
    type=click.Choice(
        [
            ToneGeneratorType.SINE.value,
            ToneGeneratorType.SAW.value,
            ToneGeneratorType.TRIANGLE.value,
            ToneGeneratorType.SQUARE.value,
        ]
    ),
    default=ToneGeneratorType.SINE,
    help=f"Type of audio tone generator used",
    show_default=True
)
@click.option(
    "--frequency", "-f", 
    type=click.FloatRange(80, 8000),
    default=800,
    help="Audio tone generator frequency",
    show_default=True
)
@click.option(
    "--sample-rate", "-r", 
    type=click.IntRange(8000, 96000), 
    default=44100,
    help="Audio output sampling rate (for playback device and WAV file)",
    show_default=True
)
@click.option(
    "--words-per-minute", "-w", 
    type=click.IntRange(5, 30),
    default=20,
    help="Determines the duration of each Morse signal",
    show_default=True
)
@click.option(
    "--debug", is_flag=True, default=False, 
    help="Show debug information?",
    show_default=True
)
@click.option(
    "--input-file", "-i",
    type=click.File("r", encoding="UTF-8"),
    help="The file to read message from. If specified, the MESSAGE argument will be ignored [Optional] [Encoding: UTF-8]",
)
@click.option(
    "--output-file", "-o",
    type=click.Path(exists=False, writable=True),
    help="The file to write audio to. If specified, audio will be written to the output file rather than played back [Optional]",
)
def cli(
    message: tuple[str],
    tone_generator_type: str,
    frequency: float,
    sample_rate: int,
    words_per_minute: int,
    debug: bool,
    input_file: TextIO,
    output_file: str,
):
    log_level = "DEBUG" if debug else "NOSHOW"
    logger.add(RichHandler(), level=log_level, format=CONSOLE_FORMAT)
    logger.debug("Logger initialized")
    
    if debug:
        console.quiet = True
    
    total_timer = Timer("Total").tic()
    
    app = App(tone_generator_type, frequency, sample_rate, words_per_minute)

    if input_file:
        message_str = input_file.read()
        logger.info(f"Message read from {input_file.name=}")
    else:
        message_str = " ".join(message)
        
    message_str = message_str.strip()
    
    if len(message_str) == 0:
        logger.critical("Cannot proceed without message!")
        app.print_no_input()
        exit(0)
        
    logger.info(f"Command invoked with message: {message_str}")
    
    app.message = message_str

    app.print_app_info()
    console.line()
    app.print_message_details()
    console.rule(style="gray50")
    app.print_unknown_characters()
    
    audio_timer = Timer("AudioDataProcessing").tic()
    
    with console.status("[gray50]Generating audio...", spinner="line2"):
        audio_data = app.generate_audio_data()
        
    logger.debug(f"{audio_timer} -> {audio_timer.toc()=}s")
    
    if output_file:
        app.save_audio_data(audio_data, output_file)
    else:
        app.play_audio_data(audio_data)
    
    logger.debug(f"{total_timer} -> {total_timer.toc()=}s")
    console.print(f"[gray50] Completed in {total_timer.toc():.2f}s", justify="right")


if __name__ == "__main__":
    cli()
