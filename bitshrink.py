import sys
import os
from collections import defaultdict
from datetime import datetime
from bitarray import bitarray

start_time = datetime.now()

def get_timestamp():
    now = datetime.now()
    diff = abs(now - start_time)
    total_seconds = int(diff.total_seconds())
    milliseconds = int((diff.total_seconds() - total_seconds) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"[{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}]" if hours <= 99 else "[99:59:59.999]+"

def read_file(file_path, mode='rb'):
    with open(file_path, mode) as f:
        return f.read()

def read_binary_file(file_path):
    ba = bitarray()
    with open(file_path, 'rb') as f:
        ba.fromfile(f)
    return ba.to01()  # Convert bitarray to a binary string

def write_binary_file(file_path, binary_data):
    """Write a binary string to a file without altering any bytes."""
    ba = bitarray(binary_data)
    with open(file_path, 'wb') as f:
        ba.tofile(f)

def read_file_as_binary_chunks(file_path, chunk_size=1024):
    chunks = []
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            chunks.append(''.join(format(byte, '08b') for byte in chunk))
    return chunks

def generate_bit_sequence(length, index):
    return format(index, f'0{length}b')

def substitute_sequence(binary_content, old_seq, new_seq):
    substituted_content = binary_content.replace(old_seq, new_seq)
    old_seq_len_bits = len(old_seq) - 1
    new_seq_len_bits = len(new_seq) - 1
    substituted_content_len_bits = len(substituted_content) - 1
    lengths = f"{new_seq_len_bits:06b}{old_seq_len_bits:08b}{substituted_content_len_bits:013b}"
    metadata = lengths + old_seq + new_seq
    return metadata + substituted_content

def resubstitute_sequence(substituted_content):
    if substituted_content[:2] == "10":
        return substituted_content[2:]  # Take the rest of the chunk as is
    new_seq_len_bits = int(substituted_content[:6], 2) + 1
    old_seq_len_bits = int(substituted_content[6:14], 2) + 1
    substituted_content_len_bits = int(substituted_content[14:27], 2) + 1
    index_old_seq = 27
    index_new_seq = index_old_seq + old_seq_len_bits
    index_last_byte = index_new_seq + new_seq_len_bits
    index_data = index_last_byte
    old_seq = substituted_content[index_old_seq:index_new_seq]
    new_seq = substituted_content[index_new_seq:index_last_byte]
    data = substituted_content[index_data:index_data + substituted_content_len_bits]
    return data.replace(new_seq, old_seq)

def substitute_repetition(binary_content, repetition, special_seq):
    repetition_length = len(repetition)
    repetition_count = repetition_length - 1
    # Ensure the repetition count fits in a single byte
    if repetition_count > 255:
        repetition_count = 255

    # Create the metadata for the substitution
    metadata = special_seq + f"{format(repetition_count, '08b')}"  # Special sequence + repetition count

    # Substitute the repetition with the special sequence + metadata
    substituted_content = binary_content.replace(repetition, metadata)
    return substituted_content

def resubstitute_repetition(substituted_content):
    if substituted_content[:3] not in ["110", "111"]:
        return substituted_content  # Not a special sequence

    repetition_count = int(substituted_content[3:11], 2) + 1
    special_seq_length = 3 + 8  # 14 bits for the special sequence + 8 bits for the count
    if substituted_content[:3] == "110":
        repetition = "0"
    else:
        repetition = "1"

    repetition *= repetition_count
    data = substituted_content[special_seq_length:]
    return repetition + data

def find_high_score_sequences(binary_content):
    max_length = 256
    best_sequences = {'00': [], '01': [], '10': [], '11': []}
    temp_best = {'00': [], '01': [], '10': [], '11': []}
    for length in range(1, max_length + 1):
        sequence_counts = defaultdict(int)
        for i in range(len(binary_content) - length + 1):
            seq = binary_content[i:i + length]
            sequence_counts[seq] += 1
        for seq, count in sequence_counts.items():
            if count > 1:
                score = length * (count - 1)
                key = seq[0] + seq[-1]
                temp_best[key].append((seq, score))
    for key, sequences in temp_best.items():
        if sequences:
            sequences.sort(key=lambda x: x[1], reverse=True)
            best_sequences[key] = sequences
    return best_sequences

def find_longest_bit_repetition(binary_content):
    """Find the longest sequence of repeated bits in the binary content."""
    max_repetition = 1
    current_repetition = 1
    longest_bit = binary_content[0]

    for i in range(1, len(binary_content)):
        if binary_content[i] == binary_content[i - 1]:
            current_repetition += 1
        else:
            if current_repetition > max_repetition:
                max_repetition = current_repetition
                longest_bit = binary_content[i - 1]
            current_repetition = 1

    # Final check in case the longest repetition ends at the last bit
    if current_repetition > max_repetition:
        max_repetition = current_repetition
        longest_bit = binary_content[-1]

    return longest_bit * max_repetition, max_repetition

def process_chunk(binary_content, max_sequence_length, total_savings, multiplier):
    best_sequences = find_high_score_sequences(binary_content)
    if not any(best_sequences.values()):
        print(f"{get_timestamp()} Error: No high-scoring sequences found within the specified maximum length.")
        return f"10{binary_content}", total_savings-2

    # Find the longest bit repetition in the chunk
    longest_repetition, repetition_length = find_longest_bit_repetition(binary_content)

    best_substitution_savings = 0
    best_substituted_content = None
    best_substitution_seq = None

    # Check if the longest repetition is worth substituting
    if repetition_length > 1:
        if longest_repetition[0] == "0":
            special_seq = "110"  # Special sequence indicator for repeating 0s
        else:
            special_seq = "111"  # Special sequence indicator for repeating 1s

        substituted_content = substitute_repetition(binary_content, longest_repetition, special_seq)
        resubstituted_content = resubstitute_repetition(substituted_content)
        if binary_content == resubstituted_content:
            savings = (len(binary_content) - len(substituted_content))
            if savings > best_substitution_savings:
                best_substitution_savings = savings
                best_substituted_content = substituted_content
                best_substitution_seq = f"Repetition: {longest_repetition}"

    for length in range(1, max_sequence_length + 1):
        print(f"\r{get_timestamp()} Trying length {length}...", end="", flush=True)
        top_sequences = []
        for edge_type, sequences in best_sequences.items():
            sequences = [seq for seq in sequences if len(seq[0]) > length]
            best_sequences[edge_type] = sequences
            if sequences:
                top_score = sequences[0][1]
                threshold_score = top_score * (1 - multiplier)
                top_sequences.extend([seq for seq, score in sequences if score >= threshold_score])
        for best_sequence in top_sequences:
            for i in range(2 ** length):
                seq = generate_bit_sequence(length, i)
                substituted_content = substitute_sequence(binary_content, best_sequence, seq)
                resubstituted_content = resubstitute_sequence(substituted_content)
                if binary_content == resubstituted_content:
                    savings = (len(binary_content) - len(substituted_content))
                    if savings > best_substitution_savings:
                        best_substitution_savings = savings
                        best_substituted_content = substituted_content
                        best_substitution_seq = f"Sequence: {best_sequence} with {seq}"

    if best_substituted_content:
        total_savings += best_substitution_savings
        print(f"{get_timestamp()} Best substitution: {best_substitution_seq}")
        print(f"{get_timestamp()} Length before substitution: {len(binary_content) // 8} bytes")
        print(f"{get_timestamp()} Length after substitution: {len(best_substituted_content) // 8} bytes")
        print(f"{get_timestamp()} Total savings: {total_savings//8} bytes")
        print(f"{get_timestamp()} Resubstitution was successful, data is the same.")
        return bitarray(best_substituted_content), total_savings

    return f"10{binary_content}", total_savings-2

def compress(file_path, output_path, max_sequence_length, multiplier):
    total_savings = 0
    binary_chunks = read_file_as_binary_chunks(file_path)
    processed_chunks = bitarray()  # Initialize an empty bitarray to store all processed chunks

    for i, chunk in enumerate(binary_chunks):
        print(f"{get_timestamp()} Processing chunk {i+1}/{len(binary_chunks)}...")
        processed_chunk, total_savings = process_chunk(chunk, max_sequence_length, total_savings, multiplier)
        processed_chunks.extend(processed_chunk)  # Append the processed chunk to the bitarray

    # Calculate and add padding if necessary
    padding_length = (8 - (len(processed_chunks) +4 % 8)) % 8  # Ensuring multiple of 8 bits
    if padding_length > 0:
        processed_chunks.extend('0' * padding_length)

    # Append padding length as a 4-bit binary number
    padding_info = format(padding_length, '04b')
    processed_chunks.extend(padding_info)

    with open(output_path, 'wb') as f:
        processed_chunks.tofile(f)  # Write the combined bitarray to the file

    print(f"{get_timestamp()} Processed file saved as {output_path}")

def extract_metadata_length(substituted_content):
    if substituted_content[:2] == "10":
        return 2 + 1024 * 8  # Fixed length for unchanged segments
    new_seq_len_bits = int(substituted_content[:6], 2) + 1
    old_seq_len_bits = int(substituted_content[6:14], 2) + 1
    substituted_content_len_bits = int(substituted_content[14:27], 2) + 1
    metadata_length = 27 + old_seq_len_bits + new_seq_len_bits
    total_bits = metadata_length + substituted_content_len_bits
    return total_bits

def decompress(file_path, output_path):
    ba = bitarray()
    with open(file_path, 'rb') as f:
        ba.fromfile(f)

    binary_data = ba.to01()  # Convert the bitarray to a binary string

    # Extract padding information (last 4 bits)
    padding_length = int(binary_data[-4:], 2)
    binary_data = binary_data[:-4]  # Remove padding information bits

    if padding_length > 0:
        binary_data = binary_data[:-padding_length]  # Remove the padding bits
    decompressed_data = ""
    while binary_data:
        if len(binary_data) < 11:
            print(f"{get_timestamp()} Warning: Remaining data is too short to contain valid metadata. Stopping decompression.")
            break

        if binary_data[:3] in ["110", "111"]:
            segment_length = 11  # Special sequence + count
        else:
            segment_length = extract_metadata_length(binary_data)

        if segment_length > len(binary_data):
            segment_length = len(binary_data)

        segment = binary_data[:segment_length]
        if segment[:3] in ["110", "111"]:
            original_content = resubstitute_repetition(segment)
        else:
            original_content = resubstitute_sequence(segment)

        decompressed_data += original_content
        binary_data = binary_data[segment_length:]

    write_binary_file(output_path, decompressed_data)
    print(f"{get_timestamp()} Decompressed file saved as {output_path}")

def process_directory(input_dir, output_dir, max_sequence_length, multiplier, mode):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(input_dir):
        input_file = os.path.join(input_dir, file_name)
        output_file = os.path.join(output_dir, file_name)

        try:
            if mode == "compress":
                compress(input_file, output_file, max_sequence_length, multiplier)
            elif mode == "decompress":
                decompress(input_file, output_file)
        except Exception as e:
            print(f"{get_timestamp()} Error processing {input_file}: {e}")
            continue

def test_compression_decompression(file_path, max_sequence_length, multiplier):
    compressed_path = file_path + ".compressed"
    decompressed_path = file_path + ".decompressed"
    compress(file_path, compressed_path, max_sequence_length, multiplier)
    decompress(compressed_path, decompressed_path)
    original_data = read_binary_file(file_path)
    decompressed_data = read_binary_file(decompressed_path)
    assert original_data == decompressed_data, "Decompressed data does not match the original data!"
    print(f"{get_timestamp()} Compression and decompression test passed!")

if __name__ == "__main__":
    if len(sys.argv) < 3 or (sys.argv[1] in ["-c", "-d"] and len(sys.argv) < 4):
        print("Usage: python bitshrink.py <-c|-d|-t> <input_file_or_directory> [<output_file_or_directory>] [optional:max_sequence_length (standard 10)] [optional:multiplier (standard 1)]")
    else:
        mode = sys.argv[1]
        input_path = sys.argv[2]
        output_path = sys.argv[3] if mode in ["-c", "-d"] else None
        max_sequence_length_index = 4 if mode in ["-c", "-d"] else 3
        multiplier_index = 5 if mode in ["-c", "-d"] else 4

        max_sequence_length = 10 if len(sys.argv) <= max_sequence_length_index else int(sys.argv[max_sequence_length_index])
        multiplier = 0.01 if len(sys.argv) <= multiplier_index else float(sys.argv[multiplier_index]) / 100

        if max_sequence_length > 32:
            max_sequence_length = 32
            print(f"{get_timestamp()} Max sequence length reset to 64")
        elif max_sequence_length < 1:
            max_sequence_length = 1
            print(f"{get_timestamp()} Max sequence length reset to 1")

        if mode == "-t":
            test_compression_decompression(input_path, max_sequence_length, multiplier)
        else:
            if os.path.isdir(input_path):
                process_directory(input_path, output_path, max_sequence_length, multiplier, "compress" if mode == "-c" else "decompress")
            else:
                if mode == "-c":
                    compress(input_path, output_path, max_sequence_length, multiplier)
                elif mode == "-d":
                    decompress(input_path, output_path)
                else:
                    print("Invalid mode. Use -c for compression, -d for decompression, and -t for testing.")