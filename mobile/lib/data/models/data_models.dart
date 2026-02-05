import 'dart:convert'; // Added for JSON encoding

class Project {
  final String id;
  final String name;
  final String type;
  final String status;
  final DateTime startDate;

  Project({
    required this.id,
    required this.name,
    required this.type,
    required this.status,
    required this.startDate,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id'],
      name: json['name'],
      type: json['type'],
      status: json['status'],
      startDate: DateTime.parse(json['start_date']),
    );
  }
}


class Milestone {
  final String id;
  final String title;
  final String status;
  final double targetPercent;

  Milestone({
    required this.id,
    required this.title,
    required this.status,
    required this.targetPercent,
  });

  factory Milestone.fromJson(Map<String, dynamic> json) {
    return Milestone(
      id: json['id'],
      title: json['title'],
      status: json['status'],
      targetPercent: double.parse(json['target_percent'].toString()),
    );
  }
}

class Inspection {
  final String? id;
  final String? milestoneId;
  final String milestoneTitle;
  final String qualityVerdict;
  final String notes;
  final DateTime inspectedAt;
  final List<String> photos;
  final Map<String, bool> icareCompliance;

  Inspection({
    this.id,
    this.milestoneId,
    required this.milestoneTitle,
    required this.qualityVerdict,
    required this.notes,
    required this.inspectedAt,
    this.photos = const [],
    this.icareCompliance = const {},
  });

  Map<String, dynamic> toMap() {
    return {
      'milestoneId': milestoneId,
      'milestoneTitle': milestoneTitle,
      'qualityVerdict': qualityVerdict,
      'notes': notes,
      'inspectedAt': inspectedAt.toIso8601String(),
      'photos': photos.join('|'),
      'icareCompliance': json.encode(icareCompliance), 
    };
  }

  factory Inspection.fromMap(Map<String, dynamic> map) {
    return Inspection(
      id: map['id']?.toString(), 
      milestoneId: map['milestoneId'],
      milestoneTitle: map['milestoneTitle'] ?? 'Unknown',
      qualityVerdict: map['qualityVerdict'],
      notes: map['notes'],
      inspectedAt: DateTime.parse(map['inspectedAt']),
      photos: (map['photos'] as String).split('|').where((s) => s.isNotEmpty).toList(),
      icareCompliance: map['icareCompliance'] != null 
          ? Map<String, bool>.from(json.decode(map['icareCompliance']))
          : {},
    );
  }
}
