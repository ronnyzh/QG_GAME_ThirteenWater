# -*- coding: utf-8 -*-
"""
Python的INI文件通用处理，暂不需要支持unicode的读写
"""
COMMENT_CHAR = '#'
SECTION_STOP_CHAR = '\n'
SECTION_START_CHAR = '['
SECTION_END_CHAR = ']'
EQUAL_CHAR = '='

class CBaseIniFile( object ):
    def __init__( self, auto_write ):
        self._auto_write = auto_write
        self._values = {}
        self._sections = []
        self._lines = []
        
        self._current_section = ''

        self._inited = self.read_file()
        
    def _get_inited( self ):
        return self._inited
        
    inited = property( _get_inited )

    def read_file( self ):
        """
        Abstract interface, need to return a bool for report a result
        """
        raise "abstract func CBaseIniFile.read_file need a implement"

    def begin_read( self ):
        '''parse initialization'''
        self._current_section = ''

    def end_read( self ):
        # add an end section tag for the last section
        if self._current_section != "":
            self._lines.append( SECTION_STOP_CHAR )

    def parse_line( self, line ):
        '''parse a line, return True for no error, or False for error occured'''
        line = line.strip()

        # empty line, skip to next line
        if line == "":
            self._lines.append( line )
            return True

        # comment line, skip to next line
        if line[0] == COMMENT_CHAR:
            self._lines.append( line )
            return True

        # parse a section
        p = line.find( EQUAL_CHAR )
        if p == -1:
            p1 = line.find( SECTION_START_CHAR )
            if p1 == -1:
                return False
            p2 = line.find( SECTION_END_CHAR, p1 )
            if p2 == -1:
                return False

            if self._current_section != '':
                self._lines.append( SECTION_STOP_CHAR )

            self._current_section = line[p1 + 1: p2].strip()
            self._sections.append( self._current_section )
            if self._current_section == "":
                return False
            else:
                self._lines.append( SECTION_START_CHAR + self._current_section + SECTION_END_CHAR )
        else:
            ident = line[: p].strip()
            value = line[p + 1:].strip()
            self._values[ ( self._current_section, ident ) ] = value
            self._lines.append( ident + EQUAL_CHAR + value )

        return True

    def begin_write( self ):
        '''return False for error raise when open file with "w" mode, or True for no error'''
        raise "abstract error: begin_write"
        
    def write_line( self, line ):
        raise "abstract error: write_line"
        
    def end_write( self ):
        raise "abstract error: end_write"

    def update_file( self ):
        """
        update INI file as new sections/ident/values
        """
        if not self.begin_write():
            return False
        try:
            section = ''
            values = self._values.copy()
            sections = [ sec for sec in self._sections ]

            for line in self._lines:
                # empty line
                if line == "":
                    self.write_line( line )
                    continue

                # comment line
                if line[0] == COMMENT_CHAR:
                    self.write_line( line )
                    continue

                # section start
                if line[0] == SECTION_START_CHAR:
                    section_name = line[1: -1]

                    if section_name in sections:
                        self.write_line( line )
                        section = section_name

                    continue

                # end section tag
                if ( line[0] == SECTION_STOP_CHAR ) and ( section != '' ):
                    if section in sections:
                        sections.remove( section )
                        keys = [ key for key in values if key[0] == section ]
                        if len(keys) > 0:
                            for key in keys:
                                ident = key[1]
                                self.write_line( '%s %s %s' % ( ident, EQUAL_CHAR, str(values[key]) ) )
                                del values[key]

                            self.write_line('')

                        continue

                # ident items
                p = line.find( EQUAL_CHAR )
                ident = line[: p]
                key = (section, ident)

                if key in values.keys():
                    self.write_line('%s %s %s' % (ident, EQUAL_CHAR, str(values[key])))
                    del values[key]

            # write new sections/ident/values
            for section in sections:
                self.write_line('[%s]' % section)

                keys = [ key for key in values if key[0] == section ]

                if len( keys ) > 0:
                    for key in keys:
                        ident = key[1]
                        self.write_line('%s %s %s' % ( ident, EQUAL_CHAR, str(values[key]) ) )
                        del values[key]

                self.write_line('')
        finally:
            self.end_write()

    def write( self, section, ident, value ):
        if type( value ) is bool:
            value = int( value )
        self._values[ (section, ident) ] = value
        if not ( section in self._sections ):
            self._sections.append( section )
        
    def read_bool( self, section, ident, default = False ):
        key = ( section, ident )
        try:
            return bool( int( self._values[key] ) )
        except:
            if self._auto_write:
                self.write( section, ident, default )
            return default
            
    def read_float( self, section, ident, default = 0.0 ):
        key = ( section, ident )
        try:
            return float( self._values[key] )
        except:
            if self._auto_write:
                self.write( section, ident, default )
            return default
            
    def read_integer( self, section, ident, default = 0 ):
        key = ( section, ident )
        try:
            return int( self._values[key] )
        except:
            if self._auto_write:
                self.write( section, ident, default )
            return default

    def read_string( self, section, ident, default = "" ):
        key = ( section, ident )
        try:
            return self._values[key]
        except:
            if self._auto_write:
                self.write( section, ident, default )
            return default
            
    def read_sections( self ):
        return tuple( self._sections )
        
    def read_idents( self, section ):
        return [ key[1] for key in self._values.keys() if key[0] == section ]
        
    def read_values( self, section ):
        return [ self._values[key] \
            for key in self._values.keys() if key[0] == section ]

    def section_exists( self, section ):
        return section in self._sections
        
    def ident_exists( self, section, ident ):
        return ( section, ident ) in self._values
        
    def delete_ident( self, section, ident ):
        key = ( section, ident )
        if key in self._values:
            del self._values[key]
            return True
        else:
            return False
        
    def delete_section( self, section ):
        if section in self._sections:
            self._sections.remove( section )

            keys = [ key for key in self._values.keys() if key[0] == section ]
            for key in keys:
                del self._values[key]
                
            return True
        else:
            return False
        
    def clear(self):
        self._values = {}
        self._sections = []
        
class CIniFile(CBaseIniFile):
    def __init__( self, filename, auto_write = True ):
        self._filename = filename
        self._unicode = False

        super(CIniFile, self).__init__( auto_write )

    def read_file( self ):
        try:
            _file = file( self._filename, "r" )
        except IOError:
            if self._auto_write:
                try:
                    _file = file( self._filename, "w" )
                except IOError:
                    return False

                _file.close()
                _file = file( self._filename, "r" )
            else:
                return False
        #head = _file.read(2)
        #print head
        #if head == '\xFF\xFE':
        #   print "Unicode"
        #   self._unicode = True
        #else:
        #   _file.seek( -2 )
        try:
            self.begin_read()

            for line in _file:
                if not self.parse_line( line ):
                    return False

            self.end_read()
        finally:
            _file.close()
            return True

    def begin_write( self ):
        try:
            self._file = file( self._filename, "w" )
            #if self._unicode:
            #   self._file.write( '\xFF\xFE' )
            return True
        except IOError:
            return False

    def write_line(self, line):
        self._file.write( line + '\n' )

    def end_write(self):
        self._file.close()

if __name__ == '__main__':
    ini = CIniFile( "test.ini" )
    t = ini.read_sections()
    ini.update_file()
    #print ini.read_string( "dlgLogin", "out_interval" )
    for section in t:
        print section
        idents = ini.read_idents( section )
        print idents
        for ident in idents:
            val = ini.read_string( section, ident )
            print val,