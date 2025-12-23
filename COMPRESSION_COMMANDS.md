# Compression Commands

## Quick Reference

### Compress Large JSON Files (Recommended)

```bash
# Compress files > 75MB in output_perturbation (keeps originals)
python3 -m src.compress_large_files output_perturbation --threshold 75

# Compress and remove originals (saves space)
python3 -m src.compress_large_files output_perturbation --threshold 75 --remove-original

# Dry run (see what would be compressed)
python3 -m src.compress_large_files output_perturbation --threshold 75 --dry-run

# Compress specific directory
python3 -m src.compress_large_files output_perturbation/20251222_223708 --threshold 50
```

### Compress All Large Files (General)

```bash
# Compress all files > 50MB (keeps originals with -k flag)
find . -type f -size +50M ! -name '*.gz' ! -path '*/.*' -exec gzip -k {} \;

# Compress and remove originals
find . -type f -size +50M ! -name '*.gz' ! -path '*/.*' -exec gzip {} \;

# Compress only JSON files > 50MB
find . -type f -name '*.json' -size +50M ! -name '*.gz' -exec gzip -k {} \;
```

### Decompress Files

```bash
# Decompress .json.gz files
python3 -m src.compress_large_files output_perturbation --decompress

# Decompress and remove .gz files
python3 -m src.compress_large_files output_perturbation --decompress --remove-compressed

# Decompress all .gz files (general)
find . -type f -name '*.gz' -exec gunzip {} \;
```

## Options

### Compression Script Options

- `--threshold THRESHOLD`: Size threshold in MB (default: 75.0)
- `--remove-original`: Remove original files after compression
- `--dry-run`: Show what would be compressed without actually compressing
- `--decompress`: Decompress .json.gz files instead of compressing
- `--remove-compressed`: When decompressing, remove compressed files

### Find Command Options

- `-size +50M`: Files larger than 50MB
- `! -name '*.gz'`: Exclude already compressed files
- `! -path '*/.*'`: Exclude hidden directories
- `-k`: Keep original file (gzip)
- `-exec gzip {} \;`: Compress each file

## Examples

### Example 1: Compress all large JSON files in output_perturbation
```bash
python3 -m src.compress_large_files output_perturbation --threshold 75
```

### Example 2: Compress and remove originals to save space
```bash
python3 -m src.compress_large_files output_perturbation --threshold 75 --remove-original
```

### Example 3: Check what would be compressed first
```bash
python3 -m src.compress_large_files output_perturbation --threshold 75 --dry-run
```

### Example 4: Compress all large files (any type) > 100MB
```bash
find . -type f -size +100M ! -name '*.gz' ! -path '*/.*' -exec gzip -k {} \;
```

## Notes

- The compression script (`src/compress_large_files.py`) is designed for JSON files
- It uses gzip compression with level 9 (maximum compression)
- Compressed files have `.gz` extension added (e.g., `file.json` → `file.json.gz`)
- The `.gitignore` is configured to ignore large uncompressed JSON files but track `.json.gz` files
- Always use `--dry-run` first to see what will be compressed

