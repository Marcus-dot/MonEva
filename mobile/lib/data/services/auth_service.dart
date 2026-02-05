import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';

// Use 10.0.2.2 for Android Emulator, localhost for iOS
// String baseUrl = 'http://10.0.2.2:8000/api/v1'; 
String baseUrl = 'http://127.0.0.1:8000/api/v1'; // iOS Simulator / Web

class AuthService {
  Future<User?> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/token/'),
      headers: {'Content-Type': 'application/json'},
      body: JSON.encode({'username': username, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final accessToken = data['access'];
      final refreshToken = data['refresh'];

      // Get user details
      final userRes = await http.get(
        Uri.parse('$baseUrl/users/me/'),
        headers: {
          'Authorization': 'Bearer $accessToken',
          'Content-Type': 'application/json',
        },
      );

      if (userRes.statusCode == 200) {
        final userData = json.decode(userRes.body);
        final user = User.fromJson(userData, accessToken, refreshToken);
        await _saveToken(accessToken, refreshToken);
        return user;
      }
    }
    return null;
  }

  Future<void> _saveToken(String access, String refresh) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', access);
    await prefs.setString('refresh_token', refresh);
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
