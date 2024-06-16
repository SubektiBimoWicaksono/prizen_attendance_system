-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jun 16, 2024 at 04:21 AM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `prizen`
--

-- --------------------------------------------------------

--
-- Table structure for table `data_izin`
--

CREATE TABLE `data_izin` (
  `izin_id` int(11) NOT NULL,
  `nama_pegawai` varchar(255) NOT NULL,
  `email_izin` varchar(100) NOT NULL,
  `keterangan` varchar(50) NOT NULL,
  `tanggal_kehadiran` date NOT NULL,
  `surat_filename` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `data_izin`
--

INSERT INTO `data_izin` (`izin_id`, `nama_pegawai`, `email_izin`, `keterangan`, `tanggal_kehadiran`, `surat_filename`) VALUES
(8, 'Subekti Bimo', 'subekti1234@gmail.com', 'Izin', '2024-06-15', 'Surat Izin KetidakHadiran.pdf'),
(9, 'Habib Ainur M', 'habibainur@gmail.com', 'Izin', '2024-06-15', 'Surat Izin KetidakHadiran.pdf');

-- --------------------------------------------------------

--
-- Table structure for table `img_dataset`
--

CREATE TABLE `img_dataset` (
  `img_id` int(11) NOT NULL,
  `wajah` varchar(18) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `img_dataset`
--

INSERT INTO `img_dataset` (`img_id`, `wajah`) VALUES
(1, '3520063012040002'),
(2, '3520063012040002'),
(3, '3520063012040002'),
(4, '3520063012040002'),
(5, '3520063012040002'),
(6, '3520063012040002'),
(7, '3520063012040002'),
(8, '3520063012040002'),
(9, '3520063012040002'),
(10, '3520063012040002'),
(11, '3520062406050002'),
(12, '3520062406050002'),
(13, '3520062406050002'),
(14, '3520062406050002'),
(15, '3520062406050002'),
(16, '3520062406050002'),
(17, '3520062406050002'),
(18, '3520062406050002'),
(19, '3520062406050002'),
(20, '3520062406050002'),
(21, '3520062406050002'),
(22, '3520062406050002'),
(23, '3520062406050002'),
(24, '3520062406050002'),
(25, '3520062406050002'),
(26, '3520062406050002'),
(27, '3520062406050002'),
(28, '3520062406050002'),
(29, '3520062406050002'),
(30, '3520062406050002'),
(31, '3520063012040002'),
(32, '3520063012040002'),
(33, '3520063012040002'),
(34, '3520063012040002'),
(35, '3520063012040002'),
(36, '3520063012040002'),
(37, '3520063012040002'),
(38, '3520063012040002'),
(39, '3520063012040002'),
(40, '3520063012040002'),
(41, '3520062301070002'),
(42, '3520062301070002'),
(43, '3520062301070002'),
(44, '3520062301070002'),
(45, '3520062301070002'),
(46, '3520062301070002'),
(47, '3520062301070002'),
(48, '3520062301070002'),
(49, '3520062301070002'),
(50, '3520062301070002'),
(51, '3520062301070002'),
(52, '3520062301070002'),
(53, '3520062301070002'),
(54, '3520062301070002'),
(55, '3520062301070002'),
(56, '3520062301070002'),
(57, '3520062301070002'),
(58, '3520062301070002'),
(59, '3520062301070002'),
(60, '3520062301070002'),
(61, '3520062301070002'),
(62, '3520062301070002'),
(63, '3520062301070002'),
(64, '3520062301070002'),
(65, '3520062301070002'),
(66, '3520062301070002'),
(67, '3520062301070002'),
(68, '3520062301070002'),
(69, '3520062301070002'),
(70, '3520062301070002');

-- --------------------------------------------------------

--
-- Table structure for table `jam_absen`
--

CREATE TABLE `jam_absen` (
  `jam_id` int(11) NOT NULL,
  `clock_in` time NOT NULL,
  `clock_out` time NOT NULL,
  `in_min` time NOT NULL,
  `in_max` time NOT NULL,
  `out_min` time NOT NULL,
  `out_max` time NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `jam_absen`
--

INSERT INTO `jam_absen` (`jam_id`, `clock_in`, `clock_out`, `in_min`, `in_max`, `out_min`, `out_max`) VALUES
(1, '17:00:00', '17:30:00', '16:55:00', '17:15:00', '21:05:00', '21:30:00');

-- --------------------------------------------------------

--
-- Table structure for table `riwayat_absensi`
--

CREATE TABLE `riwayat_absensi` (
  `absen_id` int(11) NOT NULL,
  `id_jam` int(11) NOT NULL,
  `tgl_absen` date NOT NULL,
  `id_pegawai` varchar(18) NOT NULL,
  `waktu_masuk` time NOT NULL DEFAULT current_timestamp(),
  `waktu_pulang` time NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `riwayat_absensi`
--

INSERT INTO `riwayat_absensi` (`absen_id`, `id_jam`, `tgl_absen`, `id_pegawai`, `waktu_masuk`, `waktu_pulang`) VALUES
(53, 1, '2024-06-15', '3520063012040002', '17:12:43', '18:15:28'),
(54, 1, '2024-06-15', '3520062406050002', '17:14:22', '18:15:28'),
(55, 1, '2024-06-15', '3520062301070002', '17:19:41', '18:15:30');

-- --------------------------------------------------------

--
-- Table structure for table `user_data`
--

CREATE TABLE `user_data` (
  `id_data` int(11) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `nip` varchar(18) NOT NULL,
  `nama_pegawai` varchar(50) NOT NULL,
  `role` varchar(20) NOT NULL,
  `tgl_reg` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_data`
--

INSERT INTO `user_data` (`id_data`, `username`, `password`, `email`, `nip`, `nama_pegawai`, `role`, `tgl_reg`) VALUES
(1, 'adminn', '123456', 'admin2@gmail.com', '1000010110000101', 'Administrator', 'Admin', '2023-05-27 13:52:43'),
(13, 'Muhammad Rafi', '111111', 'rafinaufal@gmail.com', '3520062301070002', 'Muhammad Rafi Naufal P', 'Pegawai', '2024-06-14 13:45:48'),
(14, 'subektibimo', '111111', 'subektibimo@gmail.com', '3520063012040002', 'Subekti Bimo Wicaksono', 'Pegawai', '2024-06-14 13:47:44'),
(15, 'habib23', '111111', 'habibainur@gmail.com', '3520062406050002', 'Habib Ainur M', 'Pegawai', '2024-06-14 13:48:45');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `data_izin`
--
ALTER TABLE `data_izin`
  ADD PRIMARY KEY (`izin_id`);

--
-- Indexes for table `img_dataset`
--
ALTER TABLE `img_dataset`
  ADD PRIMARY KEY (`img_id`);

--
-- Indexes for table `jam_absen`
--
ALTER TABLE `jam_absen`
  ADD PRIMARY KEY (`jam_id`);

--
-- Indexes for table `riwayat_absensi`
--
ALTER TABLE `riwayat_absensi`
  ADD PRIMARY KEY (`absen_id`);

--
-- Indexes for table `user_data`
--
ALTER TABLE `user_data`
  ADD PRIMARY KEY (`id_data`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `data_izin`
--
ALTER TABLE `data_izin`
  MODIFY `izin_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `img_dataset`
--
ALTER TABLE `img_dataset`
  MODIFY `img_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=199;

--
-- AUTO_INCREMENT for table `jam_absen`
--
ALTER TABLE `jam_absen`
  MODIFY `jam_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `riwayat_absensi`
--
ALTER TABLE `riwayat_absensi`
  MODIFY `absen_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=56;

--
-- AUTO_INCREMENT for table `user_data`
--
ALTER TABLE `user_data`
  MODIFY `id_data` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
