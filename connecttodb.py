from getfilemeta import sysid

def connectodb(hostname='localhost',schema='datamaster',username='root',password='',dbtype='sqlite'):
	if dbtype=='sqlite':
		import sqlite3
		conn=sqlite3.connect(schema+'.db')
		c=conn.cursor()
		c.execute("PRAGMA foreign_keys=1")
		c.executescript('''
		CREATE TABLE IF NOT EXISTS exif
		(
			exifID INTEGER PRIMARY KEY,
			exifname text UNIQUE NOT NULL
		);

		CREATE TABLE IF NOT EXISTS platforms
		(
			systemID INTEGER PRIMARY KEY,
			architecture text,
			machine text,
			node text,
			platform text,
			processor text,
			system text
		);

		CREATE TABLE IF NOT EXISTS files
		(
			fileID INTEGER PRIMARY KEY,
			filename text NOT NULL,
			pathname text UNIQUE NOT NULL,
			inode INT,
			systemID INT,
			lastmodDate text,
			lastaccessDate text,
			apparentcreationDate text,
			discovereddeletionDate text,
			insertiondate text DEFAULT CURRENT_TIMESTAMP,
			sizeInBytes INT,
			detectedformatID INT,
			ext INT,
			md5sum text,
			FOREIGN KEY (systemID) REFERENCES platforms(systemID)
		);

		CREATE TABLE IF NOT EXISTS files_exif
		(
			fileID INTEGER NOT NULL,
			exifID INTEGER NOT NULL,
			value text,
			PRIMARY KEY (exifID,fileID),
			FOREIGN KEY (fileID) REFERENCES files(fileID),
			FOREIGN KEY (exifID) REFERENCES exif(exifID)
		);
		''');
		return conn
	else:
		return None

def savesysinfotodb(dbconnect,sysinfo):
	global sysid
	if dbconnect is sqlite3.Connection:
		c=dbconnect.cursor()
		res=c.execute('''
		SELECT systemID FROM platform
		WHERE platform=?
		''',sysinfo[4])
		sysid=res.fetchAll()
		if sysid is None:
			c.execute('''
			INSERT INTO platform
			(systemID,architecture,machine,node,platform,
			processor,system)
			VALUES (?,?,?,?,?,?,?)
			''',sysinfo)
			sysid=c.lastrowid
			dbconnect.commit()
		if sysid is None:
			return False
	else:
		return False
	return True

def saveinfotodb(dbconnect,fileinfos):
	global sysid
	if dbconnect is sqlite3.Connection:
		c=dbconnect.cursor()
		for f in fileinfos:
			c.execute('''
			INSERT INTO files
			(fileID,filename,pathname,inode,systemID,
			lastmodDate,lastaccessDate,apparentcreationDate,
			discovereddeletionDate,insertiondate,sizeInBytes,
			detectedformatID,ext,md5sum)
			VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
			''',f[:-1])
			if c.lastrowid:
				fid=c.lastrowid
				for k,v in list(f[-1]):
					c.execute('''
					INSERT OR IGNORE INTO exif 
					(exifName)
					VALUES (?)
					''',(k))
					c.execute('''
					INSERT OR IGNORE INTO files_exif 
					(fileID,exifID,value)
					VALUES (?,(select exifID from exif where exifname=?),?)
					''',(fid,k,v))
			else:
				dbconnect.rollback()
				return False
		dbconnect.commit()
		return True
