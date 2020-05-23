""" addons.xml generator """

import os
from hashlib import md5


class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
    """
    ZIPS_PATH = "./repo/"
    
    def __init__( self, version ):
        # generate files
        self._generate_addons_file(version)
        self._generate_md5_file(None,version)
        self._generate_md5_zipfiles(version)
        # notify user
        print "Finished updating addons xml and md5 files"

    def _generate_addons_file( self, version ):
        # addon list
        addons = os.listdir( "./" + version + "/source/" )
        #print addons
        # final addons text
        addons_xml = u"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n"
        # loop thru and add each addons addon.xml file
        for addon in addons:
            try:
                addon = "./" + version + "/source/"+addon
				# skip any file or .svn folder
                if ( not os.path.isdir( addon ) or addon == ".svn" ): continue
                # create path
                _path = os.path.join( addon, "addon.xml" )
                #print _path
                # split lines for stripping
                xml_lines = open( _path, "r" ).read().splitlines()
                # new addon
                addon_xml = ""
                # loop thru cleaning each line
                for line in xml_lines:
                    # skip encoding format line
                    if ( line.find( "<?xml" ) >= 0 ): continue
                    # add line
                    addon_xml += unicode( line.rstrip() + "\n", "UTF-8" )
                # we succeeded so add to our final addons.xml text
                addons_xml += addon_xml.rstrip() + "\n\n"
            except Exception, e:
                # missing or poorly formatted addon.xml
                print "Excluding %s for %s" % ( _path, e, )
        # clean and add closing tag
        addons_xml = addons_xml.strip() + u"\n</addons>\n"
        # save file
        self._save_file( addons_xml.encode( "UTF-8" ), file=os.path.join("./" + version + "/", "addons.xml" ))

    def _generate_md5_file(self, fname, version):
        try:
            if fname is None: fname = "./"+version+"/addons.xml"
            # create a new md5 hash
            # m = md5.new( open( fname ).read() ).hexdigest()
            m = md5( open( fname ).read() ).hexdigest()
            # save file
            self._save_file( m, file=fname+".md5" )
        except Exception, e:
            # oops
            print "An error occurred creating md5 file!\n%s" % ( e, )

    def _save_file( self, data, file ):
        try:
            # write data to the file
            open( file, "w" ).write( data )
        except Exception, e:
            # oops
            print "An error occurred saving %s file!\n%s" % ( file, e, )
            
    def _generate_md5_zipfiles( self, version ):
        try:
            self.ZIPS_PATH = "./" + version + "/repo/"
            dirs = os.listdir( self.ZIPS_PATH )
            for dir in dirs:
                zips_path = os.path.join(self.ZIPS_PATH, dir)
                zips = os.listdir( zips_path )
                for zip_name in zips:
                    if zip_name.endswith(".zip"):
                        self._generate_md5_file (os.path.join(zips_path, zip_name ),version )
        except Exception, e:
            print "An error occurred creating md5 zip files!\n%s" % ( e, )

if ( __name__ == "__main__" ):
    # start
    Generator('helix')
    Generator('matrix')