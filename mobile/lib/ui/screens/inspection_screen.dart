import 'package:flutter/material.dart';
import '../../data/models/data_models.dart';
import '../../data/services/api_service.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

class InspectionScreen extends StatefulWidget {
  final Project project;

  const InspectionScreen({super.key, required this.project});

  @override
  State<InspectionScreen> createState() => _InspectionScreenState();
}

class _InspectionScreenState extends State<InspectionScreen> {
  final _notesController = TextEditingController();
  String _verdict = 'PASS';
  List<File> _photos = [];
  bool _submitting = false;

  final ApiService _apiService = ApiService();
  
  List<Milestone> _milestones = [];
  String? _selectedMilestoneId;
  String _selectedMilestoneTitle = '';
  bool _loadingMilestones = true;

  // I-CARE State
  final Map<String, bool> _icareCompliance = {
    'integrity': true,
    'community': true,
    'accountability': true,
    'respect': true,
    'excellence': true,
  };

  @override
  void initState() {
    super.initState();
    _fetchMilestones();
  }

  Future<void> _fetchMilestones() async {
    try {
      // NOTE: In a real app, you might want to fetch contracts first, then milestones.
      // But for MVP, assuming flatten list or direct project link.
      // Current views.py says: MilestoneViewSet filters by contract_id. Project -> Contracts -> Milestones.
      // Mobile API Service needs a better endpoint or we iterate.
      // Ideally Backend should expose /milestones/?project=ID
      // Let's assume we added that or check existing logic.
      
      // Checking backend views.py: MilestoneViewSet filters by 'contract'.
      // We don't have a direct 'project' filter on MilestoneViewSet.
      // Workaround: Get Contracts first? Or just fetch all milestones if no filter? 
      // Actually, let's just create a mock list if API fails, or better:
      // We will rely on contracts.
      
      // REVISIT: For MVP speed, I will use a placeholder fetch or just hardcode if API is tricky.
      // But we promised functionality.
      // Let's assume we can implementation the backend filter later or client-side filter.
      // Actually, let's just modify the view to accept project_id, OR fetch contracts first.
      
      // Let's do client side filtering logic in API service if needed, but for now:
      // We'll rely on the API service we just wrote.
      final milestones = await _apiService.getMilestones(widget.project.id);
      
      setState(() {
        _milestones = milestones;
        if (milestones.isNotEmpty) {
           // Default to first pending one
           try {
             final firstPending = milestones.firstWhere((m) => m.status == 'PENDING');
             _selectedMilestoneId = firstPending.id;
             _selectedMilestoneTitle = firstPending.title;
           } catch (e) {
             _selectedMilestoneId = milestones.first.id;
             _selectedMilestoneTitle = milestones.first.title;
           }
        }
        _loadingMilestones = false;
      });
    } catch (e) {
      setState(() => _loadingMilestones = false);
      // Fallback/Error handling
      print('Error fetching milestones: $e');
    }
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera);

    if (pickedFile != null) {
      setState(() {
        _photos.add(File(pickedFile.path));
      });
    }
  }

  Future<void> _submit() async {
    if (_selectedMilestoneId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a milestone.')),
      );
      return;
    }
    
    if (_photos.isEmpty && _verdict == 'FAIL') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please attach evidence for failing inspections.')),
      );
      return;
    }

    setState(() => _submitting = true);

    try {
      final inspection = Inspection(
        milestoneId: _selectedMilestoneId,
        milestoneTitle: _selectedMilestoneTitle,
        qualityVerdict: _verdict,
        notes: _notesController.text,
        inspectedAt: DateTime.now(),
        photos: _photos.map((f) => f.path).toList(),
        icareCompliance: _icareCompliance,
      );

      final success = await _apiService.submitInspection(inspection);

      if (success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Inspection Submitted!')),
          );
          Navigator.pop(context);
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to submit inspection.')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Inspect: ${widget.project.name}'),
      ),
      body: _loadingMilestones 
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_milestones.isEmpty)
              const Padding(
                padding: EdgeInsets.only(bottom: 20),
                child: Text('No milestones found for this project. Inspections require a milestone.', style: TextStyle(color: Colors.red)),
              )
            else
              DropdownButtonFormField<String>(
                value: _selectedMilestoneId,
                decoration: const InputDecoration(
                  labelText: 'Select Milestone',
                  border: OutlineInputBorder(),
                ),
                items: _milestones.map((m) {
                  return DropdownMenuItem(
                    value: m.id,
                    child: Text(
                      m.title.length > 30 ? '${m.title.substring(0, 30)}...' : m.title, 
                      overflow: TextOverflow.ellipsis
                    ),
                  );
                }).toList(),
                onChanged: (val) {
                  setState(() {
                    _selectedMilestoneId = val;
                    _selectedMilestoneTitle = _milestones.firstWhere((m) => m.id == val).title;
                  });
                },
              ),
            const SizedBox(height: 24),
            const Text(
              'Verdict',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Row(
              children: [
                Expanded(
                  child: RadioListTile<String>(
                    title: const Text('Pass'),
                    value: 'PASS',
                    groupValue: _verdict,
                    onChanged: (val) => setState(() => _verdict = val!),
                  ),
                ),
                Expanded(
                  child: RadioListTile<String>(
                    title: const Text('Fail'),
                    value: 'FAIL',
                    groupValue: _verdict,
                    onChanged: (val) => setState(() => _verdict = val!),
                    activeColor: Colors.red,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            const Text(
              'I-CARE Values Compliance',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.purple.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.purple.shade100),
              ),
              child: Column(
                children: _icareCompliance.entries.map((entry) {
                   return CheckboxListTile(
                    title: Text(_capitalize(entry.key)),
                    subtitle: Text(_getICareDesc(entry.key)),
                    value: entry.value,
                    activeColor: Colors.purple,
                    dense: true,
                    onChanged: (val) {
                      setState(() {
                        _icareCompliance[entry.key] = val!;
                      });
                    },
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _notesController,
              decoration: const InputDecoration(
                labelText: 'Notes / Observations',
                border: OutlineInputBorder(),
              ),
              maxLines: 4,
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Evidence Photos',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                TextButton.icon(
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Add Photo'),
                  onPressed: _pickImage,
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (_photos.isNotEmpty)
              SizedBox(
                height: 100,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _photos.length,
                  itemBuilder: (context, index) {
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: Stack(
                        children: [
                          Image.file(
                            _photos[index],
                            width: 100,
                            height: 100,
                            fit: BoxFit.cover,
                          ),
                          Positioned(
                            right: 0,
                            top: 0,
                            child: IconButton(
                              icon: const Icon(Icons.close, color: Colors.white, size: 20),
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              onPressed: () {
                                setState(() => _photos.removeAt(index));
                              },
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              )
            else
              Container(
                height: 100,
                color: Colors.grey[200],
                alignment: Alignment.center,
                child: const Text('No photos added'),
              ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _submitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.blue,
                foregroundColor: Colors.white,
              ),
              child: _submitting
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text('Submit Inspection', style: TextStyle(fontSize: 18)),
            ),
          ],
        ),
      ),
    );
  }

  String _capitalize(String s) => s[0].toUpperCase() + s.substring(1);

  String _getICareDesc(String key) {
    const map = {
      'integrity': 'Honesty and transparency.',
      'community': 'Engagement and respect.',
      'accountability': 'Taking ownership.',
      'respect': 'Dignity for all.',
      'excellence': 'Surpassing standards.',
    };
    return map[key] ?? '';
  }
}
