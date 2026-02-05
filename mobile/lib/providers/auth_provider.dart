import 'package:flutter/material.dart';
import '../../data/services/auth_service.dart';
import '../../data/models/user.dart';

class AuthProvider extends ChangeNotifier {
  final _authService = AuthService();
  User? _user;
  bool _isLoading = false;

  User? get user => _user;
  bool get isLoading => _isLoading;

  Future<void> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final user = await _authService.login(username, password);
      _user = user;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void logout() {
    _authService.logout();
    _user = null;
    notifyListeners();
  }
}
