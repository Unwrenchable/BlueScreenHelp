"""
file_carving.py – File signature-based recovery (file carving).

This module implements file carving - the technique of recovering files
from raw disk data by looking for file signatures, even when the file
system is corrupted or missing.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple


# ── File Signatures ─────────────────────────────────────────────────────────

@dataclass
class FileSignature:
    """File type signature definition."""
    extension: str
    mime_type: str
    header: bytes
    footer: Optional[bytes]
    max_size: int  # Maximum expected file size
    description: str


# Common file signatures for recovery
FILE_SIGNATURES = [
    # Images
    FileSignature('jpg', 'image/jpeg', b'\xFF\xD8\xFF', b'\xFF\xD9', 10 * 1024 * 1024, 'JPEG Image'),
    FileSignature('png', 'image/png', b'\x89PNG\r\n\x1a\n', b'IEND\xae\x42\x60\x82', 10 * 1024 * 1024, 'PNG Image'),
    FileSignature('gif', 'image/gif', b'GIF89a', None, 10 * 1024 * 1024, 'GIF Image'),
    FileSignature('gif', 'image/gif', b'GIF87a', None, 10 * 1024 * 1024, 'GIF Image'),
    FileSignature('bmp', 'image/bmp', b'BM', None, 50 * 1024 * 1024, 'Bitmap Image'),
    FileSignature('tif', 'image/tiff', b'II*\x00', None, 50 * 1024 * 1024, 'TIFF Image'),
    FileSignature('tif', 'image/tiff', b'MM\x00*', None, 50 * 1024 * 1024, 'TIFF Image'),

    # Documents
    FileSignature('pdf', 'application/pdf', b'%PDF-', b'%%EOF', 100 * 1024 * 1024, 'PDF Document'),
    FileSignature('docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                 b'PK\x03\x04', None, 50 * 1024 * 1024, 'Word Document'),
    FileSignature('xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                 b'PK\x03\x04', None, 50 * 1024 * 1024, 'Excel Spreadsheet'),
    FileSignature('pptx', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                 b'PK\x03\x04', None, 50 * 1024 * 1024, 'PowerPoint Presentation'),
    FileSignature('doc', 'application/msword', b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', None, 50 * 1024 * 1024, 'Word Document (Legacy)'),
    FileSignature('xls', 'application/vnd.ms-excel', b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', None, 50 * 1024 * 1024, 'Excel Spreadsheet (Legacy)'),
    FileSignature('ppt', 'application/vnd.ms-powerpoint', b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1', None, 50 * 1024 * 1024, 'PowerPoint (Legacy)'),
    FileSignature('rtf', 'application/rtf', b'{\\rtf', None, 10 * 1024 * 1024, 'Rich Text Format'),

    # Archives
    FileSignature('zip', 'application/zip', b'PK\x03\x04', None, 4 * 1024 * 1024 * 1024, 'ZIP Archive'),
    FileSignature('rar', 'application/x-rar-compressed', b'Rar!\x1a\x07', None, 4 * 1024 * 1024 * 1024, 'RAR Archive'),
    FileSignature('7z', 'application/x-7z-compressed', b'7z\xbc\xaf\x27\x1c', None, 4 * 1024 * 1024 * 1024, '7-Zip Archive'),
    FileSignature('gz', 'application/gzip', b'\x1f\x8b\x08', None, 2 * 1024 * 1024 * 1024, 'GZip Archive'),

    # Video
    FileSignature('mp4', 'video/mp4', b'\x00\x00\x00\x18ftypmp42', None, 4 * 1024 * 1024 * 1024, 'MP4 Video'),
    FileSignature('mp4', 'video/mp4', b'\x00\x00\x00\x1cftypisom', None, 4 * 1024 * 1024 * 1024, 'MP4 Video'),
    FileSignature('avi', 'video/x-msvideo', b'RIFF', b'AVI ', 4 * 1024 * 1024 * 1024, 'AVI Video'),
    FileSignature('mov', 'video/quicktime', b'\x00\x00\x00\x14ftypqt', None, 4 * 1024 * 1024 * 1024, 'QuickTime Video'),
    FileSignature('wmv', 'video/x-ms-wmv', b'\x30\x26\xB2\x75\x8E\x66\xCF\x11', None, 4 * 1024 * 1024 * 1024, 'Windows Media Video'),

    # Audio
    FileSignature('mp3', 'audio/mpeg', b'\xFF\xFB', None, 100 * 1024 * 1024, 'MP3 Audio'),
    FileSignature('mp3', 'audio/mpeg', b'ID3', None, 100 * 1024 * 1024, 'MP3 Audio with ID3'),
    FileSignature('wav', 'audio/wav', b'RIFF', b'WAVE', 200 * 1024 * 1024, 'WAV Audio'),
    FileSignature('flac', 'audio/flac', b'fLaC', None, 200 * 1024 * 1024, 'FLAC Audio'),
    FileSignature('m4a', 'audio/mp4', b'\x00\x00\x00\x20ftypM4A', None, 100 * 1024 * 1024, 'M4A Audio'),

    # Executables
    FileSignature('exe', 'application/x-msdownload', b'MZ', None, 500 * 1024 * 1024, 'Windows Executable'),
    FileSignature('dll', 'application/x-msdownload', b'MZ', None, 100 * 1024 * 1024, 'Windows DLL'),

    # Database
    FileSignature('sqlite', 'application/x-sqlite3', b'SQLite format 3\x00', None, 4 * 1024 * 1024 * 1024, 'SQLite Database'),
    FileSignature('mdb', 'application/x-msaccess', b'\x00\x01\x00\x00Standard Jet DB', None, 2 * 1024 * 1024 * 1024, 'Access Database'),

    # Text
    FileSignature('txt', 'text/plain', b'\xEF\xBB\xBF', None, 100 * 1024 * 1024, 'UTF-8 Text (BOM)'),
]


@dataclass
class CarvedFile:
    """A file found through carving."""
    offset: int  # Byte offset in the source
    size: int
    signature: FileSignature
    confidence: float  # 0.0 to 1.0


# ── File Carving Engine ────────────────────────────────────────────────────

class FileCarver:
    """Scan raw disk data for file signatures."""

    def __init__(self, signatures: Optional[List[FileSignature]] = None):
        self.signatures = signatures or FILE_SIGNATURES
        self.chunk_size = 1024 * 1024  # 1MB chunks

    def scan_data(self, data: bytes, base_offset: int = 0) -> List[CarvedFile]:
        """Scan a block of data for file signatures.

        Args:
            data: Raw data to scan
            base_offset: Offset of this data in the source (for reporting)

        Returns:
            List of carved files found
        """
        carved_files = []

        for i in range(len(data) - 16):  # Need at least 16 bytes for signatures
            for sig in self.signatures:
                if self._matches_signature(data, i, sig):
                    # Try to determine file size
                    file_size = self._estimate_file_size(data, i, sig)

                    carved_files.append(CarvedFile(
                        offset=base_offset + i,
                        size=file_size,
                        signature=sig,
                        confidence=self._calculate_confidence(data, i, sig, file_size)
                    ))

        return carved_files

    def _matches_signature(self, data: bytes, offset: int, sig: FileSignature) -> bool:
        """Check if data at offset matches a signature."""
        header_len = len(sig.header)
        if offset + header_len > len(data):
            return False

        return data[offset:offset + header_len] == sig.header

    def _estimate_file_size(self, data: bytes, offset: int, sig: FileSignature) -> int:
        """Estimate the size of a file based on its footer or heuristics.

        Args:
            data: Raw data containing the file
            offset: Start offset of the file
            sig: File signature

        Returns:
            Estimated file size in bytes
        """
        # If signature has a footer, look for it
        if sig.footer:
            footer_offset = data.find(sig.footer, offset + len(sig.header))
            if footer_offset != -1:
                return footer_offset - offset + len(sig.footer)

        # Heuristics based on file type
        if sig.extension in ['jpg', 'jpeg']:
            return self._estimate_jpeg_size(data, offset)
        elif sig.extension == 'png':
            return self._estimate_png_size(data, offset)
        elif sig.extension == 'pdf':
            return self._estimate_pdf_size(data, offset)

        # Default: scan until we hit another signature or max size
        max_scan = min(offset + sig.max_size, len(data))
        for next_offset in range(offset + len(sig.header), max_scan):
            for other_sig in self.signatures:
                if self._matches_signature(data, next_offset, other_sig):
                    return next_offset - offset

        # Return remaining data or max size
        return min(len(data) - offset, sig.max_size)

    def _estimate_jpeg_size(self, data: bytes, offset: int) -> int:
        """Find JPEG end marker (FF D9)."""
        end_marker = b'\xFF\xD9'
        end_pos = data.find(end_marker, offset)
        if end_pos != -1:
            return end_pos - offset + 2
        return min(10 * 1024 * 1024, len(data) - offset)

    def _estimate_png_size(self, data: bytes, offset: int) -> int:
        """Find PNG end chunk (IEND)."""
        end_marker = b'IEND\xae\x42\x60\x82'
        end_pos = data.find(end_marker, offset)
        if end_pos != -1:
            return end_pos - offset + 8
        return min(10 * 1024 * 1024, len(data) - offset)

    def _estimate_pdf_size(self, data: bytes, offset: int) -> int:
        """Find PDF end marker (%%EOF)."""
        end_marker = b'%%EOF'
        end_pos = data.find(end_marker, offset)
        if end_pos != -1:
            # Look for newline after EOF
            final_pos = end_pos + 5
            if final_pos < len(data) and data[final_pos] in (b'\r', b'\n'):
                final_pos += 1
            if final_pos < len(data) and data[final_pos] in (b'\r', b'\n'):
                final_pos += 1
            return final_pos - offset
        return min(100 * 1024 * 1024, len(data) - offset)

    def _calculate_confidence(self, data: bytes, offset: int,
                             sig: FileSignature, file_size: int) -> float:
        """Calculate confidence that this is a valid file.

        Args:
            data: Raw data
            offset: Start of file
            sig: File signature
            file_size: Estimated file size

        Returns:
            Confidence score 0.0 to 1.0
        """
        confidence = 0.5  # Base confidence for header match

        # Check if footer matches (if applicable)
        if sig.footer:
            footer_offset = offset + file_size - len(sig.footer)
            if (footer_offset >= 0 and
                footer_offset + len(sig.footer) <= len(data) and
                data[footer_offset:footer_offset + len(sig.footer)] == sig.footer):
                confidence += 0.3

        # Check file size is reasonable
        if 100 < file_size < sig.max_size:
            confidence += 0.1

        # Additional checks based on file type
        if sig.extension == 'pdf':
            # PDFs should contain /Type catalog references
            snippet = data[offset:offset + min(file_size, 1024)]
            if b'/Type' in snippet and b'/Catalog' in snippet:
                confidence += 0.1

        return min(1.0, confidence)


# ── Recovery Operations ────────────────────────────────────────────────────

def carve_files_from_drive(drive_handle, output_dir: Path,
                           file_types: Optional[List[str]] = None,
                           progress_callback=None) -> Dict[str, int]:
    """Carve files from a drive or disk image.

    Args:
        drive_handle: Open drive access object
        output_dir: Where to save recovered files
        file_types: Optional list of extensions to recover (e.g., ['jpg', 'pdf'])
        progress_callback: Optional callback(bytes_scanned, total_bytes)

    Returns:
        Dict with statistics: {'files_found': N, 'bytes_recovered': N}
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter signatures by requested types
    carver = FileCarver()
    if file_types:
        carver.signatures = [s for s in FILE_SIGNATURES
                            if s.extension in file_types]

    stats = {'files_found': 0, 'bytes_recovered': 0}
    chunk_size = 10 * 1024 * 1024  # 10MB chunks
    sector = 0

    while True:
        # Read chunk
        data = drive_handle.read_sectors(sector, chunk_size // 512)
        if not data or len(data) == 0:
            break

        # Scan for files
        carved = carver.scan_data(data, sector * 512)

        # Save carved files
        for carved_file in carved:
            if carved_file.confidence >= 0.6:  # Only save high-confidence files
                file_num = stats['files_found'] + 1
                filename = f"recovered_{file_num}_{carved_file.offset:016x}.{carved_file.signature.extension}"
                output_path = output_dir / filename

                try:
                    # Extract file data
                    file_data = data[carved_file.offset - sector * 512:
                                   carved_file.offset - sector * 512 + carved_file.size]

                    with open(output_path, 'wb') as f:
                        f.write(file_data)

                    stats['files_found'] += 1
                    stats['bytes_recovered'] += len(file_data)
                except Exception:
                    pass

        sector += chunk_size // 512

        if progress_callback:
            progress_callback(sector * 512, -1)

    return stats


def quick_signature_scan(data_path: Path, extensions: Optional[List[str]] = None) -> List[CarvedFile]:
    """Quick scan of a file or disk image for recoverable files.

    Args:
        data_path: Path to disk image or raw data file
        extensions: Optional list of extensions to look for

    Returns:
        List of carved files found
    """
    carver = FileCarver()

    if extensions:
        carver.signatures = [s for s in FILE_SIGNATURES if s.extension in extensions]

    all_carved = []

    with open(data_path, 'rb') as f:
        chunk_size = 10 * 1024 * 1024  # 10MB
        offset = 0

        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            carved = carver.scan_data(chunk, offset)
            all_carved.extend(carved)

            offset += len(chunk)

    return all_carved
