class PayloadTooLargeError(ValueError):
    """Redis job body exceeds configured maximum size."""

    def __init__(self, max_bytes: int, actual: int) -> None:
        super().__init__(f"Job payload exceeds {max_bytes} bytes (got {actual})")
        self.max_bytes = max_bytes
        self.actual = actual
