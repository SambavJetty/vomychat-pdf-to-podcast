import anthropic
from anthropic.types.beta.messages.batch_create_params import Request
from anthropic.types.beta.message_create_params import MessageCreateParamsNonStreaming
import os
import asyncio
from pathlib import Path
import logging
import time
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class BatchProcessor:
    def __init__(self, api_key: str, base_dir: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.base_dir = Path(base_dir)
        self.system_prompt = """You are an expert language editor specializing in optimizing text for voice synthesis. Your task is to modify the given text to make it optimal for reading aloud. 
        Follow these instructions to modify the text:
        1. Remove all numerical references, footnotes, and page numbers.
        2. Join words that are hyphenated at the end of lines.
        3. Remove excessive spaces and empty lines.
        4. Preserve correct punctuation and sentence structure.
        5. Maintain italics and other meaningful text formatting if marked.
        6. Adjust the text to be natural for reading aloud while preserving the original meaning.
        7. Return only the modified text without any comments or explanations."""

    def read_file_content(self, file_path: Path) -> str:
        """Reads the content of a text file and returns it as a string."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
            return ""
        except Exception as e:
            logging.error(f"Error reading {file_path}: {e}")
            return ""

    def write_optimized_content(self, file_path: Path, content: str) -> None:
        """Writes the optimized content to a new file."""
        try:
            optimized_path = file_path.with_name(f"{file_path.stem}-OPTIMIZED{file_path.suffix}")
            with open(optimized_path, 'w', encoding='utf-8') as file:
                file.write(content)
            logging.info(f"Successfully wrote optimized content to {optimized_path}")
        except Exception as e:
            logging.error(f"Error writing to {optimized_path}: {e}")

    def prepare_batch_requests(self, files_to_process: list[str]) -> list[Request]:
        """Prepares batch requests for processing."""
        requests = []
        self.custom_id_to_filename = {}
        for idx, filename in enumerate(files_to_process, 1):
            file_path = self.base_dir / filename
            content = self.read_file_content(file_path)

            if content:
                custom_id = f"req_{idx}"
                self.custom_id_to_filename[custom_id] = filename
                request = Request(
                    custom_id=custom_id,
                    params=MessageCreateParamsNonStreaming(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=8192,
                        temperature=0,
                        system=self.system_prompt,
                        messages=[
                            {
                                "role": "user",
                                "content": {
                                    "type": "text",
                                    "text": f"Modify the given text for voice synthesis:\n\n{content}"
                                }
                            }
                        ]
                    )
                )
                requests.append(request)
        return requests

    async def process_batch_results(self, batch_id: str, files_to_process: list[str]) -> None:
        """Processes batch results and writes optimized content."""
        try:
            pbar = tqdm(total=len(files_to_process), desc="Processing files")
            processed_files = set()
            retry_interval = 5  # seconds between status checks

            while len(processed_files) < len(files_to_process):
                # Check batch processing status
                message_batch = self.client.messages.batches.retrieve(batch_id)
                logging.info(f"Batch {message_batch.id} processing status is {message_batch.processing_status}")

                if message_batch.processing_status == "in_progress":
                    await asyncio.sleep(retry_interval)
                    continue

                if message_batch.processing_status == "ended":
                    for result in self.client.messages.batches.results(batch_id):
                        if result.custom_id in processed_files:
                            continue

                        if result.result.type == "succeeded":
                            filename = self.custom_id_to_filename[result.custom_id]
                            file_path = self.base_dir / filename
                            self.write_optimized_content(file_path, result.result.message.content[0].text)
                            processed_files.add(result.custom_id)
                            pbar.update(1)
                        elif result.result.type in {"errored", "expired"}:
                            logging.error(f"Request {result.custom_id} failed.")
                            processed_files.add(result.custom_id)
                            pbar.update(1)

                    break

            pbar.close()

        except Exception as e:
            logging.error(f"Error in batch processing: {e}")
            raise

    async def process_files(self, files_to_process: list[str]) -> None:
        """Processes files using the Message Batches API."""
        try:
            requests = self.prepare_batch_requests(files_to_process)
            if not requests:
                logging.error("No valid files to process")
                return

            message_batch = self.client.messages.batches.create(requests=requests)
            await self.process_batch_results(message_batch.id, files_to_process)

        except Exception as e:
            logging.error(f"Error in batch processing: {e}")


async def main():
    processor = BatchProcessor(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        base_dir="/path/to/your/directory"
    )
    files_to_process = ["chapter_1.md", "chapter_2.md", "chapter_3.md"]
    await processor.process_files(files_to_process)


if __name__ == "__main__":
    asyncio.run(main())
