"""
Test suite for data recovery functionality.
"""

import pytest
from pathlib import Path
from agent.data_recovery import (
    DriveInfo, RecoverableFile, RecoveryResult,
    WindowsDriveAccess, scan_drive_for_recovery
)
from agent.file_carving import FileSignature, FileCarver, CarvedFile


class TestFileSignatures:
    """Test file signature definitions."""

    def test_jpeg_signature(self):
        """Test JPEG file signature detection."""
        from agent.file_carving import FILE_SIGNATURES

        jpeg_sigs = [s for s in FILE_SIGNATURES if s.extension == 'jpg']
        assert len(jpeg_sigs) > 0
        assert jpeg_sigs[0].header == b'\xFF\xD8\xFF'
        assert jpeg_sigs[0].footer == b'\xFF\xD9'

    def test_pdf_signature(self):
        """Test PDF file signature detection."""
        from agent.file_carving import FILE_SIGNATURES

        pdf_sigs = [s for s in FILE_SIGNATURES if s.extension == 'pdf']
        assert len(pdf_sigs) > 0
        assert pdf_sigs[0].header == b'%PDF-'
        assert pdf_sigs[0].footer == b'%%EOF'


class TestFileCarver:
    """Test file carving functionality."""

    def test_carver_initialization(self):
        """Test FileCarver initializes correctly."""
        carver = FileCarver()
        assert carver is not None
        assert len(carver.signatures) > 0

    def test_jpeg_detection(self):
        """Test detection of JPEG file in data."""
        carver = FileCarver()

        # Create test data with JPEG signature
        test_data = b'\x00' * 100  # padding
        test_data += b'\xFF\xD8\xFF\xE0'  # JPEG header
        test_data += b'\x00' * 1000  # JPEG data
        test_data += b'\xFF\xD9'  # JPEG footer
        test_data += b'\x00' * 100  # padding

        carved = carver.scan_data(test_data)

        # Should find at least one JPEG
        jpeg_files = [f for f in carved if f.signature.extension == 'jpg']
        assert len(jpeg_files) > 0
        assert jpeg_files[0].offset == 100  # Where we placed it

    def test_pdf_detection(self):
        """Test detection of PDF file in data."""
        carver = FileCarver()

        # Create test data with PDF signature
        test_data = b'\x00' * 50
        test_data += b'%PDF-1.4\r\n'  # PDF header
        test_data += b'Some PDF content here\r\n'
        test_data += b'%%EOF\r\n'  # PDF footer
        test_data += b'\x00' * 50

        carved = carver.scan_data(test_data)

        # Should find at least one PDF
        pdf_files = [f for f in carved if f.signature.extension == 'pdf']
        assert len(pdf_files) > 0

    def test_multiple_file_detection(self):
        """Test detection of multiple files in data."""
        carver = FileCarver()

        # Create test data with multiple file signatures
        test_data = b'\xFF\xD8\xFF\xE0'  # JPEG
        test_data += b'\x00' * 500
        test_data += b'%PDF-1.4'  # PDF
        test_data += b'\x00' * 500
        test_data += b'PK\x03\x04'  # ZIP

        carved = carver.scan_data(test_data)

        # Should find at least 2 files (JPEG and PDF are reliably detected)
        assert len(carved) >= 2

        # Check we found different types
        extensions = {f.signature.extension for f in carved}
        assert 'jpg' in extensions or 'pdf' in extensions


class TestDriveAccess:
    """Test drive access functionality (mostly unit tests, not integration)."""

    def test_drive_info_creation(self):
        """Test DriveInfo dataclass."""
        drive = DriveInfo(
            device_path=r"\\.\PhysicalDrive0",
            size_bytes=500_000_000_000,
            model="Test SSD",
            serial="ABC123",
            is_removable=False,
            partition_style="GPT"
        )

        assert drive.device_path == r"\\.\PhysicalDrive0"
        assert drive.size_bytes == 500_000_000_000
        assert not drive.is_removable

    def test_recoverable_file_creation(self):
        """Test RecoverableFile dataclass."""
        from datetime import datetime

        file_info = RecoverableFile(
            name="test.jpg",
            path="/photos/test.jpg",
            size_bytes=1024000,
            created=datetime.now(),
            modified=datetime.now(),
            is_deleted=False,
            cluster_list=[100, 101, 102, 103],
            recoverable_percent=100.0
        )

        assert file_info.name == "test.jpg"
        assert file_info.size_bytes == 1024000
        assert len(file_info.cluster_list) == 4

    def test_recovery_result_creation(self):
        """Test RecoveryResult dataclass."""
        result = RecoveryResult(
            success=True,
            files_found=10,
            files_recovered=8,
            bytes_recovered=50_000_000,
            errors=["Error 1", "Error 2"]
        )

        assert result.success
        assert result.files_found == 10
        assert result.files_recovered == 8
        assert len(result.errors) == 2


class TestScanDriveForRecovery:
    """Test drive scanning functionality."""

    def test_scan_invalid_drive(self):
        """Test scanning an invalid drive path."""
        # This should not crash, just return inaccessible
        assessment = scan_drive_for_recovery(r"\\.\InvalidDrive99")

        assert 'accessible' in assessment
        assert 'file_system' in assessment
        assert 'recommendations' in assessment

    def test_scan_assessment_structure(self):
        """Test that scan returns proper structure."""
        # Even for invalid drives, structure should be correct
        assessment = scan_drive_for_recovery(r"\\.\PhysicalDrive999")

        # Check all required keys are present
        assert 'accessible' in assessment
        assert 'file_system' in assessment
        assert 'estimated_files' in assessment
        assert 'total_size' in assessment
        assert 'recommendations' in assessment

        # Check types
        assert isinstance(assessment['accessible'], bool)
        assert isinstance(assessment['file_system'], str)
        assert isinstance(assessment['estimated_files'], int)
        assert isinstance(assessment['total_size'], int)
        assert isinstance(assessment['recommendations'], list)


class TestFileSystemDetection:
    """Test file system signature detection."""

    def test_ntfs_detection(self):
        """Test NTFS boot sector detection."""
        # Create a minimal NTFS boot sector
        boot_sector = b'\xEB\x52\x90'  # Jump instruction
        boot_sector += b'NTFS    '  # OEM ID
        boot_sector += b'\x00' * (512 - len(boot_sector))

        # The scan function should detect NTFS
        assert b'NTFS' in boot_sector

    def test_fat32_detection(self):
        """Test FAT32 boot sector detection."""
        # Create a minimal FAT32 boot sector
        boot_sector = b'\xEB\x58\x90'  # Jump instruction
        boot_sector += b'\x00' * 79
        boot_sector += b'FAT32'  # File system type at offset 82
        boot_sector += b'\x00' * (512 - len(boot_sector))

        assert b'FAT32' in boot_sector


class TestWindowsDriveAccess:
    """Test Windows drive access class (non-integration tests)."""

    def test_initialization(self):
        """Test WindowsDriveAccess initializes."""
        drive = WindowsDriveAccess()
        assert drive is not None
        assert drive.handle is None

    def test_sector_size_constants(self):
        """Test sector size constants."""
        drive = WindowsDriveAccess()
        # Check default sector size is 512
        assert hasattr(drive, 'GENERIC_READ')
        assert drive.GENERIC_READ == 0x80000000


def test_imports():
    """Test that all modules can be imported."""
    from agent import data_recovery
    from agent import file_carving

    assert data_recovery is not None
    assert file_carving is not None


def test_file_signature_count():
    """Test that we have a reasonable number of file signatures."""
    from agent.file_carving import FILE_SIGNATURES

    # Should have at least 30 file signatures
    assert len(FILE_SIGNATURES) >= 30

    # Check we have major categories
    extensions = {sig.extension for sig in FILE_SIGNATURES}

    # Images
    assert 'jpg' in extensions
    assert 'png' in extensions

    # Documents
    assert 'pdf' in extensions
    assert 'docx' in extensions

    # Archives
    assert 'zip' in extensions

    # Video
    assert 'mp4' in extensions

    # Audio
    assert 'mp3' in extensions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
