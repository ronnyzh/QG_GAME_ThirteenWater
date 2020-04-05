# -*- coding: utf-8 -*-
"""
Python的csv文件解析
"""

CSV_QUOTED = '"'
CSV_DELIMITER = ','

class Csv( object ):
    """ csv file object, use to parse csv file"""
    def __init__( self, iterator ):
        """
        call the contruct by params for line of csv file
        """
        self._records = []
        try:
            while True:
                record = self._get_record( iterator )
                self._records.append( record )
        except StopIteration:
            pass

    def _get_pos( self, string, sub_string ):
        try:
            return string.index( sub_string )
        except ValueError:
            return -1

    def _parse_value( self, line, iterator ):
        result = ''
        line = line[1: ]

        while True:
            pq = self._get_pos( line, CSV_QUOTED )
            while pq == -1:
                result = ''.join( [ result, line, '\n' ] )

                try:
                    line = iterator.next()
                except StopIteration:
                    raise ValueError, "imcomplete csv table!"

                pq = self._get_pos( line, CSV_QUOTED )

            result += line[: pq]
            line = line[pq + 1: ]

            if line != '' and line[0] == CSV_QUOTED:
                result += CSV_QUOTED
                line = line[1: ]
            else:
                if line != '' and line[0] == CSV_DELIMITER:
                    line = line[1: ]
                line = line.lstrip()

                break

        return result, line

    def _get_record( self, iterator ):
        line = iterator.next()

        record = []
        while line != '':
            if line[0] == CSV_QUOTED:
                value, line = self._parse_value( line, iterator )
            else:
                p = self._get_pos( line, CSV_DELIMITER )
                if p == -1:
                    value = line.strip()
                    line = ''
                else:
                    value = line[: p]
                    line = line[p + 1: ]

                    if line == '':
                        record.append( value )
                        value = ''

            record.append( value )

        return record

    def __len__( self ):
        """ you can use 'len( obj )' access the row count in the csv file"""
        return len( self._records )

    def __getitem__( self, index ):
        """ you can use 'obj[ index ]' access each row in the csv file"""
        return self._records[ index ]

    def __iter__( self ):
        """ use a csv object as an iterator """
        def records():
            for record in self._records:
                yield record

        return records()
        
def file_iterator( filename ):
    def iterator():
        for line in file(filename):
            yield line[: -1]

    return iterator()

def csv_mapping( iterator, convertors = [] ):
    """
    pair test case
    """
    csv = Csv( iterator )

    convertor_count = len( convertors )
    if convertor_count < 2:
        convertors.extend( [None] * (2 - convertor_count) )
    elif convertor_count > 2:
        convertors = convertors[: 2]

    self_convector = lambda x: x
    convertors = [ (convertor and convertor or self_convector) \
        for convertor in convertors ]

    keyvalues = [ (convertors[0](record[0]), \
        (len(record) > 1) and convertors[1](record[1]) or None) \
        for record in csv ]

    return dict( keyvalues )

if __name__ == '__main__':
    def mapping_test():
        m = csv_mapping( file_iterator(r'ranks.csv'), [int] )
        for key, value in m.iteritems():
            print key, value

    mapping_test()