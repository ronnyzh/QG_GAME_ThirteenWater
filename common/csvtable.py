# -*- coding: utf-8 -*-
"""
Python的csv文件行表数据提取处理
"""

class CsvTable( object ):
    """
    csv file read data, general you only need to call $table = CsvTable( filepath, default_converters, check_func )
    to read a csv file and construct a table{$id : $row_datas}, and than you can expand all row data by: for row in $table,
    or you can directly access one row_data by call $talbe[ $id ].
    """

    # a init row data class
    class CsvRow( object ):
        def __getitem__( self, key ):
            """ you can use 'obj[ key ]' access each record in the csv row"""
            return self.__dict__[ key ]

        def __setitem__( self, key, val ):
            """ you can use to implement assignment for 'obj[ key ] = val' """
            setattr( self, key, val )

    def __init__( self, filename, convertors = [], checker = None ):
        self._filename = filename

        import csvfile
        table = csvfile.Csv( csvfile.file_iterator( filename ) )

        _iter = table.__iter__()
        fields = _iter.next()
        field_count = len( fields )

        convertor_count = len( convertors )
        # print field_count
        if convertor_count < field_count:
            convertors.extend( [None] * ( field_count - convertor_count ) )
        elif convertor_count > field_count:
            convertors = convertors[: field_count]

        self_convector = lambda x: x
        convertors = [ (convertor and convertor or self_convector) \
            for convertor in convertors ]

        # row instance
        self._records = []
        # id to row_data dict
        self._id2row = {}
        # fields order
        self._fields = fields[:]

        checker = checker and checker or ( lambda x: True )

        line = 0
        # each row
        for record in _iter:
            record_size = len( record )
            if record_size < field_count:
                record.extend( [''] * ( field_count - record_size ) )
            elif record_size > field_count:
                record = record[: field_count]

            # check data valid
            if not checker(record):
                raise ValueError, "record %s failed in checking" % (record, )

            inst = CsvTable.CsvRow()

            for field, value, convertor in zip( fields, record, convertors ):
                setattr( inst, field, convertor(value) )

            key = fields[0]
            # check duplicate
            assert inst[key] not in self._id2row, "line[%ld] id[%s] has already set [%s]"%( line, inst[key], self._id2row[inst[key]].__dict__ )
            # check type
            assert type( inst[key] ) == convertors[0], "line [%ld] id[%s] is not default type[%s]"%( line, inst[key], convertors[0] )
            self._id2row[ inst[key] ] = inst
            self._records.append( inst )
            line += 1

    def get_data_by_row_and_column( self, row, column ):
        assert (row > 0) and (row < self.get_record_count() + 2) 
        assert (column > 0) and (column < len(self._fields) + 1)
        if ( row == 1 ):
            return self._fields[column-1]
        else:
            r = self._records[row-2]
            return r[self._fields[column-1]]

    def set_data_by_row_and_column( self, row, column, value ):
        assert (row > 1) and (row < self.get_record_count() + 2)
        assert (column > 0) and (column < len(self._fields) + 1)
        self._records[row-2][self._fields[column-1]] = str(value)
    
    def get_record_count( self ):
        return self.__len__()
    
    def get_row( self, row ):
        return self.__getitem__( row )
            
    def update_file( self ):
        try:
            _file = file( self._filename, "w" )
        except IOError:
            return False

        _file.write( ','.join( self._fields ) + '\n' )
        for row in self._records:
            _file.write( ','.join( [ str( row[field] )for field in self._fields ] ) + '\n' )

        _file.flush()
        _file.close()

        return True

    def __len__(self):
        """ you can use 'len( obj )' access the record count in the csv table"""
        return len( self._records )

    def __getitem__( self, idx ):
        """ you can use 'obj[ idx ]' access each record in the csv table"""
        return self._id2row[ idx ]

    def __iter__(self):
        """ use a csv table as an iterator """
        def iterator():
            for record in self._records:
                yield record

        return iterator()
            
if __name__ == '__main__':
    def checker(record):
        try:
            return int( record[11] ) == int( record[12] ) * 100 and \
                int( record[14] ) == int( record[15] ) and \
                int( record[17] ) == int( record[18] )
        except:
            return False

    table = CsvTable( r'ShopGoods.csv', [ int, str ] )#, checker )
    print table.get_data_by_row_and_column( 85,3 )
    table.set_data_by_row_and_column(85,21,2)
    table.update_file()
    print table.get_data_by_row_and_column( 2,3 )
    record = table[ 11001 ]
    print record["商品名称"]
    record["商品名称"] = "老式手雷"
    print record["商品名称"]
    table.update_file()
    t = CsvTable(r'user_names.csv', [ str, str, str, str ] )
    c = t.get_data_by_row_and_column(2,1)
    print c
    print t[c].__dict__
    #for record in table:
    #   print record.__dict__
