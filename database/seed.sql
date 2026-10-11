USE facial_attendance;

-- CLEAR EXISTING SEED DATA SAFELY (Order handles FK constraints)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE attendance;
TRUNCATE TABLE attendance_sessions;
TRUNCATE TABLE face_embeddings;
TRUNCATE TABLE staff_class_allocation;
TRUNCATE TABLE notifications;
TRUNCATE TABLE audit_logs;
TRUNCATE TABLE students;
TRUNCATE TABLE staff;
SET FOREIGN_KEY_CHECKS = 1;

-- INSERT STAFF MEMBERS (CSE001 - CSE011)
-- Default Password: Password123
INSERT INTO staff (staff_id, name, email, password_hash, department) VALUES
('CSE001', 'Dr. Alan Turing', 'alan.turing@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE002', 'Dr. Grace Hopper', 'grace.hopper@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE003', 'Prof. John von Neumann', 'john.neumann@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE004', 'Prof. Ada Lovelace', 'ada.lovelace@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE005', 'Dr. Claude Shannon', 'claude.shannon@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE006', 'Dr. Tim Berners-Lee', 'tim.lee@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE007', 'Prof. Donald Knuth', 'donald.knuth@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE008', 'Dr. Barbara Liskov', 'barbara.liskov@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE009', 'Dr. Edsger Dijkstra', 'edsger.dijkstra@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE010', 'Dr. Leslie Lamport', 'leslie.lamport@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE'),
('CSE011', 'Dr. Andrew Ng', 'andrew.ng@college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE');

-- INSERT STUDENTS (23CSR001 - 23CSR003)
-- Default Password: Password123
INSERT INTO students (student_id, name, email, password_hash, department, year, section, phone) VALUES
('23CSR001', 'NANTHITHA P', 'nanthitha@student.college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE', 4, 'C', '9876543210'),
('23CSR002', 'ALICE JOHNSON', 'alice@student.college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE', 4, 'C', '9876543211'),
('23CSR003', 'BOB SMITH', 'bob@student.college.edu', 'scrypt:32768:8:1$DFb8CBn6fjA77b1q$cd33409a7c0e8060569535b0068a0df40fe908e43e2946f296b9586047dcd8bc35e9c12e16e3937cc9c94d210661d497ce3035adc5d0a39c94a174632563fafb', 'CSE', 4, 'C', '9876543212');

-- INSERT STAFF CLASS ALLOCATIONS (CSE, Year 4, Section C)
-- Mon - Sat, Hours 1 to 7 with distinct staff allocations
INSERT INTO staff_class_allocation (staff_id, department, year, section, day, subject, hour) VALUES
-- MONDAY
('CSE011', 'CSE', 4, 'C', 'Monday', 'Deep Learning', 1),
('CSE001', 'CSE', 4, 'C', 'Monday', 'Machine Learning', 2),
('CSE002', 'CSE', 4, 'C', 'Monday', 'Cloud Computing', 3),
('CSE003', 'CSE', 4, 'C', 'Monday', 'Database Security', 4),
('CSE004', 'CSE', 4, 'C', 'Monday', 'Neural Networks', 5),
('CSE005', 'CSE', 4, 'C', 'Monday', 'Computer Vision', 6),
('CSE006', 'CSE', 4, 'C', 'Monday', 'Software Engineering', 7),

-- TUESDAY
('CSE001', 'CSE', 4, 'C', 'Tuesday', 'Machine Learning', 1),
('CSE011', 'CSE', 4, 'C', 'Tuesday', 'Deep Learning', 2),
('CSE005', 'CSE', 4, 'C', 'Tuesday', 'Computer Vision', 3),
('CSE007', 'CSE', 4, 'C', 'Tuesday', 'Data Structures', 4),
('CSE008', 'CSE', 4, 'C', 'Tuesday', 'Cyber Security', 5),
('CSE002', 'CSE', 4, 'C', 'Tuesday', 'Cloud Computing', 6),
('CSE009', 'CSE', 4, 'C', 'Tuesday', 'Mobile Computing', 7),

-- WEDNESDAY
('CSE002', 'CSE', 4, 'C', 'Wednesday', 'Cloud Computing', 1),
('CSE003', 'CSE', 4, 'C', 'Wednesday', 'Database Security', 2),
('CSE011', 'CSE', 4, 'C', 'Wednesday', 'Deep Learning', 3),
('CSE004', 'CSE', 4, 'C', 'Wednesday', 'Neural Networks', 4),
('CSE006', 'CSE', 4, 'C', 'Wednesday', 'Software Engineering', 5),
('CSE001', 'CSE', 4, 'C', 'Wednesday', 'Machine Learning', 6),
('CSE010', 'CSE', 4, 'C', 'Wednesday', 'Distributed Systems', 7),

-- THURSDAY
('CSE004', 'CSE', 4, 'C', 'Thursday', 'Neural Networks', 1),
('CSE005', 'CSE', 4, 'C', 'Thursday', 'Computer Vision', 2),
('CSE001', 'CSE', 4, 'C', 'Thursday', 'Machine Learning', 3),
('CSE011', 'CSE', 4, 'C', 'Thursday', 'Deep Learning', 4),
('CSE007', 'CSE', 4, 'C', 'Thursday', 'Data Structures', 5),
('CSE008', 'CSE', 4, 'C', 'Thursday', 'Cyber Security', 6),
('CSE002', 'CSE', 4, 'C', 'Thursday', 'Cloud Computing', 7),

-- FRIDAY
('CSE005', 'CSE', 4, 'C', 'Friday', 'Computer Vision', 1),
('CSE006', 'CSE', 4, 'C', 'Friday', 'Software Engineering', 2),
('CSE007', 'CSE', 4, 'C', 'Friday', 'Data Structures', 3),
('CSE003', 'CSE', 4, 'C', 'Friday', 'Database Security', 4),
('CSE011', 'CSE', 4, 'C', 'Friday', 'Deep Learning', 5),
('CSE004', 'CSE', 4, 'C', 'Friday', 'Neural Networks', 6),
('CSE001', 'CSE', 4, 'C', 'Friday', 'Machine Learning', 7),

-- SATURDAY
('CSE008', 'CSE', 4, 'C', 'Saturday', 'Cyber Security', 1),
('CSE009', 'CSE', 4, 'C', 'Saturday', 'Mobile Computing', 2),
('CSE010', 'CSE', 4, 'C', 'Saturday', 'Distributed Systems', 3),
('CSE011', 'CSE', 4, 'C', 'Saturday', 'Deep Learning', 4),
('CSE002', 'CSE', 4, 'C', 'Saturday', 'Cloud Computing', 5),
('CSE005', 'CSE', 4, 'C', 'Saturday', 'Computer Vision', 6),
('CSE007', 'CSE', 4, 'C', 'Saturday', 'Data Structures', 7);
