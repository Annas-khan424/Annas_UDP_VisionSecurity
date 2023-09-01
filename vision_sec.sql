
-- Database: `vision_sec`
--

-- --------------------------------------------------------

--
-- Table structure for table `students`
--

CREATE TABLE `students` (
  `student_id` int(11) NOT NULL,
  `student_name` varchar(255) NOT NULL,
  `course_end_date` date NOT NULL,
  `password` varchar(255) NOT NULL,
  `photo_path` varchar(255) NOT NULL,
  `qr_code_path` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`student_id`, `student_name`, `course_end_date`, `password`, `photo_path`, `qr_code_path`) VALUES
(534, 'sharuk', '2023-12-22', '534', 'uploads/sharuk_photo.jpg', 'uploads/sharuk_qrcode.png'),
(234614, 'khan', '2023-08-31', 'anas123', 'uploads/khan_photo.jpg', 'uploads/khan_qrcode.png'),
(243448, 'sejal', '2025-02-13', 'sejal123', 'uploads/sejal_photo.jpg', 'uploads/sejal_qrcode.png');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `students`
--
ALTER TABLE `students`
  ADD PRIMARY KEY (`student_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `students`
--
ALTER TABLE `students`
  MODIFY `student_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=346439;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
