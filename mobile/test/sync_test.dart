import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:shared_preferences/shared_preferences.dart'; // Added
import 'package:mobile/data/services/api_service.dart';
import 'package:mobile/data/services/database_helper.dart';
import 'package:mobile/data/models/data_models.dart';
import 'sync_test.mocks.dart';

// Generate MockDatabaseHelper
@GenerateMocks([DatabaseHelper])
void main() {
  late MockDatabaseHelper mockDbHelper;
  late TestApiService apiService;

  setUp(() {
    mockDbHelper = MockDatabaseHelper();
    apiService = TestApiService(dbHelper: mockDbHelper);
  });

  test('syncPendingInspections should fetch from DB, send to backend, and delete from DB', () async {
    // Arrange
    final inspectionData = {
      'id': 1,
      'milestoneTitle': 'Foundation',
      'qualityVerdict': 'Pass',
      'notes': 'Good',
      'inspectedAt': DateTime.now().toIso8601String(),
      'photos': '' // Empty for simplicity
    };
    
    // Stub getPendingInspections to return one item
    when(mockDbHelper.getPendingInspections())
        .thenAnswer((_) async => [inspectionData]);

    // Stub deleteInspection
    when(mockDbHelper.deleteInspection(1))
        .thenAnswer((_) async => 1);

    // Act
    await apiService.syncPendingInspections();

    // Assert
    // Verify backend send was called (TestApiService does this implicitly, but we can check side effects)
    verify(mockDbHelper.getPendingInspections()).called(1);
    
    // Verify delete was called with ID 1
    verify(mockDbHelper.deleteInspection(1)).called(1);
  });

  test('Integration: Real API call to localhost:8000', () async {
      // 1. Mock Token
      SharedPreferences.setMockInitialValues({
          'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY5ODU4MTE4LCJpYXQiOjE3Njk4NTc4MTgsImp0aSI6ImJmNGU5ZTkxZjQ5MzQ1ZDRhOWQyZWVhYzVhMWVkMmMzIiwidXNlcl9pZCI6ImNkNjJiYjEwLWQ4ZTEtNGViOC1iNzQ2LWI4MWM4YjBmOWU1ZSJ9.9DLBDkcMYos_h1VtRgfW2X3e1DTNSET2hY-ZAa8a9U4' 
      });

      // 2. Create Dummy File
      final tempDir = Directory.systemTemp;
      final file = File('${tempDir.path}/test_image.jpg');
      await file.writeAsBytes([0, 1, 2, 3]); // Dummy bytes

      // 3. Create Inspection
      final inspection = Inspection(
          id: '999',
          milestoneId: 'ea5be269-7604-477e-88a7-970d6be3a30c', // Valid ID from backend
          milestoneTitle: 'Integration Test',
          qualityVerdict: 'PASS', // Valid UpperCase Choice
          notes: 'Automated Test Note',
          inspectedAt: DateTime.now(),
          photos: [file.path]
      );

      // 4. Use Real ApiService (no override)
      // Mocks needed for construction, but not used for sendToBackend
      final mockDb = MockDatabaseHelper(); 
      final realApiService = ApiService(dbHelper: mockDb);

      // 5. Call sendToBackend
      try {
        final success = await realApiService.sendToBackend(inspection);
        expect(success, true);
      } catch (e) {
          print('Integration Error: $e');
          rethrow; // Fail test
      }
  });
}

// Subclass to mock the HTTP call
class TestApiService extends ApiService {
  TestApiService({required DatabaseHelper dbHelper}) : super(dbHelper: dbHelper);

  @override
  Future<bool> sendToBackend(Inspection inspection) async {
    // Simulate successful backend call
    return true;
  }
}
