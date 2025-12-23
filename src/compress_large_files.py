#!/usr/bin/env python3
"""
Utility to compress large JSON files to reduce size for git.
Compresses files larger than the specified threshold (default: 75 MB).
"""
import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import List, Tuple


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB."""
    return file_path.stat().st_size / (1024 * 1024)


def compress_json_file(file_path: Path, remove_original: bool = False) -> Tuple[bool, float, float]:
    """
    Compress a JSON file using gzip.
    
    Args:
        file_path: Path to JSON file
        remove_original: If True, remove original file after compression
        
    Returns:
        Tuple of (success, original_size_mb, compressed_size_mb)
    """
    try:
        original_size = get_file_size_mb(file_path)
        
        # Read original JSON
        with open(file_path, 'rb') as f_in:
            data = f_in.read()
        
        # Write compressed version
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        with gzip.open(compressed_path, 'wb', compresslevel=9) as f_out:
            f_out.write(data)
        
        compressed_size = get_file_size_mb(compressed_path)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        # Remove original if requested
        if remove_original:
            file_path.unlink()
        
        return True, original_size, compressed_size
    except Exception as e:
        print(f"Error compressing {file_path}: {e}", file=sys.stderr)
        return False, 0.0, 0.0


def find_large_json_files(
    directory: Path,
    threshold_mb: float = 75.0,
    recursive: bool = True
) -> List[Tuple[Path, float]]:
    """
    Find all JSON files larger than threshold.
    
    Args:
        directory: Directory to search
        threshold_mb: Size threshold in MB
        recursive: Search recursively
        
    Returns:
        List of (file_path, size_mb) tuples
    """
    large_files = []
    
    if recursive:
        pattern = "**/*.json"
    else:
        pattern = "*.json"
    
    for json_file in directory.glob(pattern):
        # Skip already compressed files
        if json_file.suffix == '.gz' or json_file.name.endswith('.json.gz'):
            continue
        
        # Skip if compressed version exists
        if (json_file.parent / f"{json_file.name}.gz").exists():
            continue
        
        try:
            size_mb = get_file_size_mb(json_file)
            if size_mb >= threshold_mb:
                large_files.append((json_file, size_mb))
        except Exception:
            continue
    
    return sorted(large_files, key=lambda x: x[1], reverse=True)


def decompress_json_file(compressed_path: Path, remove_compressed: bool = False) -> Tuple[bool, float]:
    """
    Decompress a gzipped JSON file.
    
    Args:
        compressed_path: Path to .json.gz file
        remove_compressed: If True, remove compressed file after decompression
        
    Returns:
        Tuple of (success, decompressed_size_mb)
    """
    try:
        # Determine output path (remove .gz extension)
        if compressed_path.suffix == '.gz':
            output_path = compressed_path.with_suffix('')
        else:
            output_path = compressed_path.parent / compressed_path.stem
        
        # Decompress
        with gzip.open(compressed_path, 'rb') as f_in:
            data = f_in.read()
        
        with open(output_path, 'wb') as f_out:
            f_out.write(data)
        
        decompressed_size = get_file_size_mb(output_path)
        
        # Remove compressed if requested
        if remove_compressed:
            compressed_path.unlink()
        
        return True, decompressed_size
    except Exception as e:
        print(f"Error decompressing {compressed_path}: {e}", file=sys.stderr)
        return False, 0.0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compress large JSON files to reduce size for git"
    )
    parser.add_argument(
        "directory",
        type=str,
        nargs="?",
        default="output_perturbation",
        help="Directory to search for large JSON files (default: output_perturbation)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=75.0,
        help="Size threshold in MB (default: 75.0)"
    )
    parser.add_argument(
        "--remove-original",
        action="store_true",
        help="Remove original files after compression (default: keep original)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be compressed without actually compressing"
    )
    parser.add_argument(
        "--decompress",
        action="store_true",
        help="Decompress .json.gz files instead of compressing"
    )
    parser.add_argument(
        "--remove-compressed",
        action="store_true",
        help="When decompressing, remove compressed files after decompression"
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist", file=sys.stderr)
        sys.exit(1)
    
    if args.decompress:
        # Decompress mode
        compressed_files = list(directory.rglob("*.json.gz"))
        if not compressed_files:
            print("No compressed .json.gz files found.")
            return
        
        print(f"Found {len(compressed_files)} compressed file(s) to decompress\n")
        total_original_size = 0.0
        
        for compressed_file in sorted(compressed_files):
            success, decompressed_size = decompress_json_file(
                compressed_file,
                remove_compressed=args.remove_compressed
            )
            if success:
                total_original_size += decompressed_size
                action = "Decompressed and removed" if args.remove_compressed else "Decompressed"
                print(f"✓ {action}: {compressed_file.name}")
                print(f"  Size: {decompressed_size:.2f} MB")
            else:
                print(f"✗ Failed: {compressed_file.name}")
        
        print(f"\nTotal decompressed: {total_original_size:.2f} MB")
    else:
        # Compress mode
        large_files = find_large_json_files(directory, args.threshold)
        
        if not large_files:
            print(f"No JSON files found larger than {args.threshold} MB in {directory}")
            return
        
        print(f"Found {len(large_files)} file(s) larger than {args.threshold} MB:\n")
        
        total_original_size = 0.0
        total_compressed_size = 0.0
        
        for file_path, size_mb in large_files:
            print(f"{file_path.relative_to(directory)}: {size_mb:.2f} MB")
            total_original_size += size_mb
        
        if args.dry_run:
            print(f"\n[DRY RUN] Would compress {len(large_files)} file(s)")
            print(f"Total size: {total_original_size:.2f} MB")
            return
        
        print(f"\nCompressing {len(large_files)} file(s)...\n")
        
        for file_path, size_mb in large_files:
            success, original_size, compressed_size = compress_json_file(
                file_path,
                remove_original=args.remove_original
            )
            
            if success:
                total_compressed_size += compressed_size
                compression_ratio = (1 - compressed_size / original_size) * 100
                action = "Compressed and removed" if args.remove_original else "Compressed"
                print(f"✓ {action}: {file_path.relative_to(directory)}")
                print(f"  Original: {original_size:.2f} MB → Compressed: {compressed_size:.2f} MB ({compression_ratio:.1f}% reduction)")
            else:
                print(f"✗ Failed: {file_path.relative_to(directory)}")
        
        total_reduction = (1 - total_compressed_size / total_original_size) * 100
        print(f"\nSummary:")
        print(f"  Files processed: {len(large_files)}")
        print(f"  Original total: {total_original_size:.2f} MB")
        print(f"  Compressed total: {total_compressed_size:.2f} MB")
        print(f"  Total reduction: {total_reduction:.1f}%")
        
        if not args.remove_original:
            print(f"\nNote: Original files kept. Use --remove-original to delete them after compression.")


if __name__ == "__main__":
    main()

