import os

from empowerb.settings import MEDIA_ROOT


class EDIFileHandler:

    def __init__(self, filename):
        try:
            self._filename = filename
            self._file = os.path.join(MEDIA_ROOT, filename)
            self._segment_txt = ''
            self.terminator = ''

            with open(self.file, 'r') as reader:
                # read the file content
                self._content = reader.read()
                # derive separator (for raw edi)
                self._separator = self.content[3]
                last_header_field = self._content.split(self._separator)[16]
                last_splitted_elem = last_header_field.split("GS")
                if len(last_splitted_elem) == 2:
                    if len(last_splitted_elem[0]) == 2:
                        self.terminator = last_splitted_elem[0][-1]
                    else:
                        if '~' in last_splitted_elem[0]:
                            self.terminator = '~'
                        elif '\n' in last_splitted_elem[0]:
                            self.terminator = '\n'
                        else:
                            self.terminator = last_splitted_elem[0][1]
                else:
                    self.terminator = last_splitted_elem[1]
                # get segments list splitted by terminator char (in this case break line)
                self._segments = self.content.split(self.terminator)

                # main structure (could be useful in future validations)
                self._ISA = self.segments[0]
                self._GS = self.segments[1]
                self._ST = self.segments[2]

                # print(f"ISA Segment - {self._ISA}")
                # print(f"GS Segment - {self._GS}")
                # print(f"ST Segment - {self._ST}")

                # doctype
                self._doctype = self.ST.split(self.separator)[1]

        except Exception as ex:
            print(ex.__str__())

    @property
    def filename(self):
        return self._filename

    @property
    def file(self):
        return self._file

    @property
    def content(self):
        return self._content

    @property
    def separator(self):
        return self._separator

    @property
    def segments(self):
        return self._segments

    @property
    def ISA(self):
        return self._ISA

    @property
    def GS(self):
        return self._GS

    @property
    def ST(self):
        return self._ST

    @property
    def doctype(self):
        return self._doctype

    @property
    def segment_txt(self):
        return self._segment_txt

    def parse_current_segment_txt(self, row):

        try:
            # segment id
            segment_id = self.segment_txt[0]  # get segment id in the first position

            # init position (after segment id)
            col = len(segment_id) + 2

            elements = []
            for index, value in enumerate(self.segment_txt[1:], start=1):
                index = str(index).zfill(2)
                elements.append({
                    'id': f'{segment_id}{index}',
                    'value': value,
                    'row': row,
                    'col': col,
                    'chars': len(value),
                })

                col += len(value) + 1

            return {
                'id': segment_id,
                'elements': elements
            }

        except Exception as ex:
            print(ex.__str__())
            return None

    def get_segment_list(self):

        segments_list = []
        for row, elem in enumerate(self.segments, start=1):
            # update current segment txt
            self._segment_txt = elem.split(self.separator)
            # parse current segment txt
            segment_dict = self.parse_current_segment_txt(row)
            # add object to the list
            segments_list.append(segment_dict)

        return segments_list
