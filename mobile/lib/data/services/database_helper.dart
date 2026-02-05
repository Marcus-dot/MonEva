import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('moneva.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(path, version: 2, onCreate: _createDB, onUpgrade: _onUpgrade);
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestoneId TEXT,
        milestoneTitle TEXT,
        qualityVerdict TEXT,
        notes TEXT,
        inspectedAt TEXT,
        photos TEXT,
        icareCompliance TEXT
      )
    ''');
  }

  Future _onUpgrade(Database db, int oldVersion, int newVersion) async {
    if (oldVersion < 2) {
      await db.execute('ALTER TABLE inspections ADD COLUMN icareCompliance TEXT');
    }
  }

  Future<int> insertInspection(Map<String, dynamic> row) async {
    final db = await instance.database;
    return await db.insert('inspections', row);
  }

  Future<List<Map<String, dynamic>>> getPendingInspections() async {
    final db = await instance.database;
    return await db.query('inspections');
  }

  Future<int> deleteInspection(int id) async {
    final db = await instance.database;
    return await db.delete('inspections', where: 'id = ?', whereArgs: [id]);
  }
}
