class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const processorOptions = options?.processorOptions ?? {};
    this.chunkSize = processorOptions.chunkSize ?? 2560;
    this.minFlushSize = processorOptions.minFlushSize ?? 720;
    this.buffer = new Float32Array(0);

    this.port.onmessage = (event) => {
      if (event.data?.type === 'flush') {
        this.flush();
      }
      if (event.data?.type === 'reset') {
        this.buffer = new Float32Array(0);
      }
    };
  }

  process(inputs) {
    const input = inputs[0]?.[0];
    if (!input) {
      return true;
    }

    const merged = new Float32Array(this.buffer.length + input.length);
    merged.set(this.buffer, 0);
    merged.set(input, this.buffer.length);
    this.buffer = merged;

    while (this.buffer.length >= this.chunkSize) {
      const chunk = this.buffer.slice(0, this.chunkSize);
      this.port.postMessage({ type: 'chunk', payload: chunk }, [chunk.buffer]);
      this.buffer = this.buffer.slice(this.chunkSize);
    }

    return true;
  }

  flush() {
    if (this.buffer.length >= this.minFlushSize) {
      const chunk = this.buffer.slice(0);
      this.port.postMessage({ type: 'chunk', payload: chunk }, [chunk.buffer]);
    }
    this.buffer = new Float32Array(0);
  }
}

registerProcessor('audio-capture-processor', AudioCaptureProcessor);
