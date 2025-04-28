#!/usr/bin/python3
import ctypes
import datetime
import os
import platform
import socket

def connect(host=None, port=0, user='admin', password='admin', database=None):
	if host != None:
		host = host.encode("utf-8")
	if database != None:
		database = database.encode("utf-8")
	return CrossDbConnection(host, port, user.encode("utf-8"), password.encode("utf-8"), database)

def load_crossdb():
	sys = platform.system()
	if sys == 'Linux':
		if os.path.exists('./libcrossdb.so'):
			return ctypes.cdll.LoadLibrary('./libcrossdb.so')
		else:
			return ctypes.cdll.LoadLibrary('libcrossdb.so')
	elif sys == 'Windows':
		if os.path.exists('./libcrossdb.dll'):
			return ctypes.cdll.LoadLibrary('./libcrossdb.dll')
		else:
			return ctypes.cdll.LoadLibrary('libcrossdb.dll')

class CrossDbType(object):
	XDB_TYPE_TINYINT	= 1
	XDB_TYPE_SMALLINT	= 2
	XDB_TYPE_INT		= 3
	XDB_TYPE_BIGINT	 	= 4
	XDB_TYPE_FLOAT	   	= 9
	XDB_TYPE_DOUBLE	 	= 10
	XDB_TYPE_CHAR		= 12
	XDB_TYPE_VCHAR		= 14
	XDB_TYPE_BOOL		= 16
	XDB_TYPE_INET		= 17

class CrossDbInterface(object):
	libCrossdb = load_crossdb()
	libCrossdb.xdb_open.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_open.restype = ctypes.c_void_p
	libCrossdb.xdb_connect.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_connect.restype = ctypes.c_void_p
	libCrossdb.xdb_close.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_exec.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
	libCrossdb.xdb_exec.restype = ctypes.c_void_p
	libCrossdb.xdb_fetch_row.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_fetch_row.restype = ctypes.c_void_p
	libCrossdb.xdb_free_result.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_commit.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_rollback.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_affected_rows.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_row_count.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_column_count.argtypes = [ctypes.c_void_p]
	libCrossdb.xdb_column_type.argtypes = [ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_column_name.argtypes = [ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_column_name.restype = ctypes.c_char_p
	libCrossdb.xdb_column_int.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_column_str.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_column_str.restype = ctypes.c_char_p
	libCrossdb.xdb_column_bool.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_column_bool.restype = ctypes.c_bool
	libCrossdb.xdb_col_double.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_col_double.restype = ctypes.c_double
	libCrossdb.xdb_column_inet.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]
	libCrossdb.xdb_column_inet.restype = ctypes.c_char_p
	libCrossdb.xdb_inet_sprintf.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint16]

class CrossDbConnection(object):
	def __init__(self, host, port, user, password, database):
		self._hConn = ctypes.c_void_p()
		if CrossDbInterface.libCrossdb == None:
			self._hDb == None
			print ("Can't open CrossDb library")
			return
		self._hConn = CrossDbInterface.libCrossdb.xdb_connect (host, user, password, database, port)
		if self._hConn == None:
			print ("Can't open connection")

	def __del__(self):
		self.close ()

	def cursor(self):
		if self._hConn == None:
			return None
		return CrossDbCursor(self._hConn)

	def close(self):
		if self._hConn != None:
			CrossDbInterface.libCrossdb.xdb_close (self._hConn)

	def commit(self):
		CrossDbInterface.libCrossdb.xdb_commit (self._hConn)

	def rollback(self):
		CrossDbInterface.libCrossdb.xdb_rollback (self._hConn)

class CrossDbCursor(object):
	def __init__(self, hConn):
		self._hConn = hConn
		self._libCrossdb = CrossDbInterface.libCrossdb
		self._hResult = None
		self._valBuf = ctypes.create_string_buffer(128)

	def __del__(self):
		self.close()

	def __iter__(self):
		return self

	def next(self):
		return self.__next__()

	def __next__(self):
		row = self.fetchone()
		if None == row:
			raise StopIteration
		return row

	@property
	def rowcount(self):
		return self._libCrossdb.xdb_row_count(self._hResult)

	@property
	def affected_rows(self):
		return self._libCrossdb.xdb_affected_rows(self._hResult)

	@property
	def description(self):
		self._description = []
		if self._hResult > 0:
			for i in range (self._fldCount):
				colType = self._libCrossdb.xdb_column_type(self._hResult, i)
				colName = self._libCrossdb.xdb_column_name(self._hResult, i)
				self._description.append ((colName, colType, None, None, None, None, False))		
		return self._description

	def close(self):
		if self._hResult != None:
			self._libCrossdb.xdb_free_result(self._hResult)
			self._hResult = None

	def execute(self, sql):
		if self._hResult != None:
			self._libCrossdb.xdb_free_result(self._hResult)
		self._hResult = self._libCrossdb.xdb_exec (self._hConn, sql.encode("utf-8"))
		self._errno = ctypes.cast(self._hResult + 4, ctypes.POINTER(ctypes.c_uint16))[0]
		self._fldCount = self._libCrossdb.xdb_column_count (self._hResult)
		if self._fldCount > 0:
			self._fieldType = []
			for i in range (self._fldCount):
				colType = self._libCrossdb.xdb_column_type(self._hResult, i)
				self._fieldType.append (colType)
		return self._errno

	def fetchone(self):
		row = []
		xrow = self._libCrossdb.xdb_fetch_row(self._hResult)
		if None == xrow:
			return None
		for i in range (self._fldCount):
			type = self._fieldType[i]
			value = None
			if CrossDbType.XDB_TYPE_INT == type or CrossDbType.XDB_TYPE_SMALLINT == type or CrossDbType.XDB_TYPE_TINYINT == type:
				value = self._libCrossdb.xdb_column_int(self._hResult, xrow, i)
			elif CrossDbType.XDB_TYPE_CHAR == type or CrossDbType.XDB_TYPE_VCHAR == type:
				value = self._libCrossdb.xdb_column_str(self._hResult, xrow, i)
			elif CrossDbType.XDB_TYPE_FLOAT == type or CrossDbType.XDB_TYPE_DOUBLE == type:
				value = self._libCrossdb.xdb_column_double(self._hResult, xrow, i)
			elif CrossDbType.XDB_TYPE_BOOL == type:
				value = self._libCrossdb.xdb_column_bool(self._hResult, xrow, i)
			elif CrossDbType.XDB_TYPE_INET == type:
				inet = self._libCrossdb.xdb_column_inet(self._hResult, xrow, i)
				self._libCrossdb.xdb_inet_sprintf(inet, self._valBuf, 128)
				value = self._valBuf.value
			else:
				print ("Unknow type: "+str(type))
			row.append (value)
		return row

	def fetchall(self):
		rows=[]
		while True:
			row = self.fetchone ()
			if None == row:
				break;
			rows.append (row)
		return rows

	def executemany(self, operation, seq_of_parameters):
		pass

	def fetchmany(self):
		pass

	def commit(self):
		self._libCrossdb.xdb_commit (self._hConn)

	def rollback(self):
		self._libCrossdb.xdb_rollback (self._hConn)

	def callproc(self, procname, *args):
		pass

if __name__ == '__main__':

	conn = connect(database=":memory:")
	cursor = conn.cursor()
	cursor.execute("CREATE TABLE student (name CHAR(16), age INT, class CHAR(16), male BOOL)")
	cursor.execute("INSERT INTO student (name,age,class,male) VALUES ('jack',10,'3-1', false), ('rose',11,'2-5', true)")
	print ("insert rows: ", cursor.affected_rows)	
	cursor.execute("SELECT * from student")
	print ("select row count: ", cursor.rowcount)
	names = [description[0] for description in cursor.description]
	print ("columns: ", names)
	print ("rows:")
	for row in cursor:
		print (row)
	cursor.close()
	#cursor.execute("SHELL")
