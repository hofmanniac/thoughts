
import re

from thoughts.engine import Context
from thoughts.operations.core import Operation

class DocumentSplitter(Operation):
    def __init__(self, max_chunk_size=300, overlap=100):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def split_into_sentences(self, text):
        # Split text into sentences using a regex that identifies sentence boundaries
        sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
        sentences = sentence_endings.split(text)
        return sentences

    def execute(self, context: Context, text):
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = []

        current_chunk_size = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            if current_chunk_size + sentence_length > self.max_chunk_size:
                # If adding this sentence exceeds max_chunk_size, finalize the current chunk
                chunks.append(' '.join(current_chunk))
                # Start a new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.overlap)
                current_chunk = current_chunk[overlap_start:]
                current_chunk_size = sum(len(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_chunk_size += sentence_length
        
        # Add the last chunk if it contains any sentences
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
