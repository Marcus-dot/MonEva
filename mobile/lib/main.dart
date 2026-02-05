import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'ui/screens/login_screen.dart';
import 'ui/screens/home_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: const MonEvaApp(),
    ),
  );
}

class MonEvaApp extends StatelessWidget {
  const MonEvaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MonEva',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
      },
    );
  }
}
