import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../../data/models/data_models.dart';
import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import '../../data/services/database_helper.dart';


// Use 10.0.2.2 for Android Emulator, localhost for iOS/Web
const String baseUrl = 'http://10.0.2.2:8000/api/v1'; 

class ApiService {
  final DatabaseHelper _dbHelper;
  
  ApiService({DatabaseHelper? dbHelper}) : _dbHelper = dbHelper ?? DatabaseHelper.instance;

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  Future<List<Project>> getProjects() async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/projects/'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Project.fromJson(json)).toList();
    }
    throw Exception('Failed to load projects');
  }

  Future<List<Milestone>> getMilestones(String projectId) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/milestones/?project=$projectId'), // Assuming filtering works this way based on views.py
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Milestone.fromJson(json)).toList();
    }
    throw Exception('Failed to load milestones');
  }

  // Extracted for overriding in tests
  Future<bool> sendToBackend(Inspection inspection) async {
    final token = await _getToken();
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/inspections/'));
    request.headers['Authorization'] = 'Bearer $token';

    // Milestone logic needs proper mapping, for now just notes
    request.fields['milestone'] = inspection.milestoneId ?? ''; 
    request.fields['quality_verdict'] = inspection.qualityVerdict;
    request.fields['notes'] = inspection.notes;
    request.fields['inspected_at'] = inspection.inspectedAt.toIso8601String();
    
    // I-CARE Integration
    request.fields['icare_compliance'] = json.encode(inspection.icareCompliance);

    for (var path in inspection.photos) {
      if (await File(path).exists()) {
        request.files.add(await http.MultipartFile.fromPath('photos', path));
      }
    }

    var response = await request.send();
    return response.statusCode == 201;
  }

  Future<bool> submitInspection(Inspection inspection) async {
    var connectivityResult = await (Connectivity().checkConnectivity());
    if (connectivityResult == ConnectivityResult.none) {
      // Offline: Save to DB
      await _dbHelper.insertInspection(inspection.toMap());
      return true; // Assume success (stored locally)
    } else {
      // Online: Try to send
      bool success = await sendToBackend(inspection);
      if (!success) {
        // Fallback: Save to DB
        await _dbHelper.insertInspection(inspection.toMap());
        return true; 
      }
      // Also try to sync pending
      await syncPendingInspections();
      return success;
    }
  }

  Future<void> syncPendingInspections() async {
    var pending = await _dbHelper.getPendingInspections();
    for (var row in pending) {
      final inspection = Inspection.fromMap(row);
      // Ensure we have the ID to delete
      final id = row['id']; 
      bool success = await sendToBackend(inspection);
      if (success && id != null) {
        await _dbHelper.deleteInspection(id);
      }
    }
  }
}
