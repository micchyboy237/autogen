import logging
from typing import Any, Callable, Optional
from autogen.io.base import IOStream

logger = logging.getLogger(__name__)


class CapturingIOStream(IOStream):
    def __init__(self):
        self.output_buffer = []
        self.persistent_log = []
        self.flush_listener: Optional[Callable[[str], None]] = None

    def set_flush_listener(self, listener: Callable[[str], None]) -> None:
        self.flush_listener = listener

    def print(self, *objects: Any, sep: str = " ", end: str = "\n", flush: bool = False) -> None:
        output = sep.join(map(str, objects)) + end
        self.output_buffer.append(output)
        if flush:
            self.flush()

    def input(self, prompt: str = "", *, password: bool = False) -> str:
        # Call parent class method
        return super().input(prompt, password=password)

    def flush(self):
        output = ''.join(self.output_buffer)
        self.persistent_log.append(output)
        if self.flush_listener:
            self.flush_listener(output)
        self.output_buffer.clear()

    def get_output(self) -> str:
        return ''.join(self.persistent_log)


if __name__ == "__main__":
    def flush_listener(output: str) -> None:
        print(f"Flushed Output: {output}")

    # Set the custom IOStream as the global default
    capturing_iostream = CapturingIOStream()
    capturing_iostream.set_flush_listener(flush_listener)
    IOStream.set_global_default(capturing_iostream)
    # IOStream.set_default(capturing_iostream)

    # Example usage
    iostream = IOStream.get_default()
    iostream.print("Hello, world!", end="", flush=True)
    iostream.print("This is a test.", end="", flush=True)

    # Access the captured output
    captured_output = capturing_iostream.get_output()
    print("Captured Output:")
    print(captured_output)
