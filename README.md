
# BitShrink 🚀

Welcome to **BitShrink** - your friendly bit-crunching buddy! Compress and decompress files with ease using our efficient bit sequence substitution logic.

## What is BitShrink?

BitShrink finds bit sequences that can be substituted with shorter sequences, compressing your files without losing any data. It's like ghost, but with bits! 🌟

## How to Use

### Basic Commands

- **Compress a file:**
  ```sh
  python bitshrink.py -c <input_file> <output_file>
  ```

- **Decompress a file:**
  ```sh
  python bitshrink.py -d <input_file> <output_file>
  ```

- **Test compression and decompression:**
  ```sh
  python bitshrink.py -t <input_file>
  ```

### Optional Arguments

- **Max Sequence Length:** Set the maximum bit sequence length to check (default is `10`).
- **Top Scored Sequences:** Set the percentage of top scored sequences to check within each 1024-byte chunk (default is `1%`).

Example with optional arguments:
```sh
python bitshrink.py -c <input_file> <output_file> 15 5
```
This sets the max sequence length to `15` and checks the top `5%` scored sequences.

### Why These Options Matter?

- **Max Sequence Length:** Longer sequences might give better compression but take more time to analyze.
- **Top Scored Sequences:** Adjust the percentage to balance between compression quality and speed.

## Get Started

Clone the repo, make sure you have Python installed, and start shrinking those bits!

```sh
git clone https://github.com/RAZZULLIX/bitshrink.git
cd bitshrink
python bitshrink.py -c example.txt example.shrinked
```

### License

BitShrink is released under the GPL v3 license. See the LICENSE file for more details.

---

Enjoy compressing with BitShrink! 🎉

## Acknowledgments 🙏

- God for the ideas
- Sonic (custom GPT-4 instance) for the code
- The open-source community for continuous inspiration and collaboration
