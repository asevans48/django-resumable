# -*- coding: utf-8 -*-
import fnmatch

from django.core.files.base import ContentFile


class ResumableFile(object):
    def __init__(self, storage, kwargs):
        self.storage = storage
        self.kwargs = kwargs
        self.chunk_suffix = "_part_"

    @property
    def chunk_exists(self):
        """Checks if the requested chunk exists.
        """
        return self.storage.exists("%s%s%s" % (
            self.filename,
            self.chunk_suffix,
            self.kwargs.get('resumableChunkNumber')
        ))

    @property
    def chunks(self):
        """Iterates over all stored chunks.
        """
        chunks = []
        for file in self.storage.listdir('')[1]:
            if fnmatch.fnmatch(file, '%s%s*' % (self.filename,
                    self.chunk_suffix)):
                chunks.append(file)
        return chunks

    def delete_chunks(self):
        [self.storage.delete(chunk) for chunk in self.chunks]

    @property
    def file(self):
        """Gets the complete file.
        """
        if not self.is_complete:
            raise Exception('Chunk(s) still missing')
        content = ''
        for chunk in self.chunks:
            content += self.storage.open(chunk).read()
        return ContentFile(content)

    @property
    def filename(self):
        """Gets the filename."""
        filename = self.kwargs.get('resumableFilename')
        if '/' in filename:
            raise Exception('Invalid filename')
        return "%s_%s" % (
            self.kwargs.get('resumableTotalSize'),
            filename
        )

    @property
    def is_complete(self):
        """Checks if all chunks are allready stored.
        """
        if self.storage.exists(self.filename):
            return True
        return int(self.kwargs.get('resumableTotalSize')) == self.size

    def process_chunk(self, file):
        if not self.chunk_exists:
            self.storage.save('%s%s%s' % (
                self.filename,
                self.chunk_suffix,
                self.kwargs.get('resumableChunkNumber')
            ), file)

    @property
    def size(self):
        """Gets chunks size.
        """
        size = 0
        for chunk in self.chunks:
            size += self.storage.size(chunk)
        return size
