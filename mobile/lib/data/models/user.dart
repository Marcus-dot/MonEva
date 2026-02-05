class User {
  final String id;
  final String username;
  final String email;
  final String role;
  final String token;
  final String refresh;

  User({
    required this.id,
    required this.username,
    required this.email,
    required this.role,
    required this.token,
    required this.refresh,
  });

  factory User.fromJson(Map<String, dynamic> json, String accessToken, String refreshToken) {
    // Decode JWT or fetch user details separately? 
    // For MVP, assume we fetch /users/me/ after login or backend returns user details on login.
    // The Standard SimpleJWT only returns access/refresh.
    // So we need to: Login -> Get Token -> Get /users/me/
    
    return User(
      id: json['id'] ?? '',
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      role: json['role'] ?? 'INSPECTOR',
      token: accessToken,
      refresh: refreshToken,
    );
  }
}
