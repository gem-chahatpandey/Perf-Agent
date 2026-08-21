import pytest
from pathlib import Path
from app.storage.filesystem import FilesystemStorage


@pytest.fixture
def tmp_storage(tmp_path):
    return FilesystemStorage(base_dir=tmp_path)


class TestFilesystemStorage:
    @pytest.mark.asyncio
    async def test_save_and_load(self, tmp_storage):
        await tmp_storage.save("test/data.json", {"key": "value"})
        result = await tmp_storage.load("test/data.json")
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_exists(self, tmp_storage):
        assert not await tmp_storage.exists("missing.json")
        await tmp_storage.save("exists.json", {"x": 1})
        assert await tmp_storage.exists("exists.json")

    @pytest.mark.asyncio
    async def test_list(self, tmp_storage):
        await tmp_storage.save("runs/run1/meta.json", {"id": "1"})
        await tmp_storage.save("runs/run2/meta.json", {"id": "2"})
        items = await tmp_storage.list("runs")
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_delete(self, tmp_storage):
        await tmp_storage.save("to_delete.json", {"x": 1})
        assert await tmp_storage.exists("to_delete.json")
        await tmp_storage.delete("to_delete.json")
        assert not await tmp_storage.exists("to_delete.json")

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, tmp_storage):
        with pytest.raises(ValueError, match="traversal"):
            await tmp_storage.save("../../etc/passwd", {"hack": True})

    @pytest.mark.asyncio
    async def test_save_and_load_file(self, tmp_storage):
        await tmp_storage.save_file("binary/test.bin", b"hello bytes")
        result = await tmp_storage.load_file("binary/test.bin")
        assert result == b"hello bytes"
