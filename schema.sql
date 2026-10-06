-- 복복이(WelBot) DB 스키마 (데이터 제외)
CREATE DATABASE IF NOT EXISTS `welbot_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `welbot_db`;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;


CREATE TABLE `applmetlist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `servId` varchar(50) DEFAULT NULL,
  `servSeCode` varchar(50) DEFAULT NULL,
  `servSeDetailNm` varchar(200) DEFAULT NULL,
  `servSeDetailLink` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `servId` (`servId`),
  CONSTRAINT `applmetList_ibfk_1` FOREIGN KEY (`servId`) REFERENCES `servlist` (`servId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `basfrmlist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `servId` varchar(50) DEFAULT NULL,
  `servSeCode` varchar(50) DEFAULT NULL,
  `servSeDetailNm` varchar(200) DEFAULT NULL,
  `servSeDetailLink` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `servId` (`servId`),
  CONSTRAINT `basfrmList_ibfk_1` FOREIGN KEY (`servId`) REFERENCES `servlist` (`servId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `baslawlist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `servId` varchar(50) DEFAULT NULL,
  `servSeCode` varchar(50) DEFAULT NULL,
  `servSeDetailNm` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `servId` (`servId`),
  CONSTRAINT `baslawList_ibfk_1` FOREIGN KEY (`servId`) REFERENCES `servlist` (`servId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `chat_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` varchar(100) DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `chat_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `inqplctadrlist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `servId` varchar(50) DEFAULT NULL,
  `servSeCode` varchar(50) DEFAULT NULL,
  `servSeDetailNm` varchar(200) DEFAULT NULL,
  `servSeDetailLink` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `servId` (`servId`),
  CONSTRAINT `inqplCtadrList_ibfk_1` FOREIGN KEY (`servId`) REFERENCES `servlist` (`servId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `inqplhmpgreldlist` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `servId` varchar(50) DEFAULT NULL,
  `servSeCode` varchar(50) DEFAULT NULL,
  `servSeDetailNm` varchar(200) DEFAULT NULL,
  `servSeDetailLink` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `servId` (`servId`),
  CONSTRAINT `inqplHmpgReldList_ibfk_1` FOREIGN KEY (`servId`) REFERENCES `servlist` (`servId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `median_income` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `year` int(11) DEFAULT NULL,
  `household_size` int(11) DEFAULT NULL,
  `monthly_income` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_year_size` (`year`,`household_size`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `servdetail` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `servId` varchar(50) DEFAULT NULL,
  `servNm` varchar(200) DEFAULT NULL,
  `jurMnofNm` varchar(100) DEFAULT NULL,
  `tgtrDtlCn` text DEFAULT NULL,
  `slctCritCn` text DEFAULT NULL,
  `alwServCn` text DEFAULT NULL,
  `crtrYr` varchar(10) DEFAULT NULL,
  `rprsCtadr` varchar(200) DEFAULT NULL,
  `wlfareInfoOutlCn` text DEFAULT NULL,
  `sprtCycNm` varchar(100) DEFAULT NULL,
  `srvPvsnNm` varchar(100) DEFAULT NULL,
  `lifeArray` varchar(500) DEFAULT NULL,
  `trgterIndvdlArray` varchar(500) DEFAULT NULL,
  `intrsThemaArray` varchar(500) DEFAULT NULL,
  `updated_at` datetime DEFAULT current_timestamp(),
  `sprtTrgtCn` text DEFAULT NULL,
  `aplyMtdCn` text DEFAULT NULL,
  `enfcBgngYmd` varchar(20) DEFAULT NULL,
  `enfcEndYmd` varchar(20) DEFAULT NULL,
  `aplyMtdNm` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `servId` (`servId`),
  CONSTRAINT `servDetail_ibfk_1` FOREIGN KEY (`servId`) REFERENCES `servlist` (`servId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `servlist` (
  `servId` varchar(50) NOT NULL,
  `servNm` varchar(200) DEFAULT NULL,
  `jurMnofNm` varchar(100) DEFAULT NULL,
  `jurOrgNm` varchar(100) DEFAULT NULL,
  `servDgst` text DEFAULT NULL,
  `servDtlLink` varchar(500) DEFAULT NULL,
  `sprtCycNm` varchar(100) DEFAULT NULL,
  `srvPvsnNm` varchar(100) DEFAULT NULL,
  `onapPsbltYn` varchar(1) DEFAULT NULL,
  `rprsCtadr` varchar(200) DEFAULT NULL,
  `inqNum` int(11) DEFAULT 0,
  `lifeArray` varchar(500) DEFAULT NULL,
  `intrsThemaArray` varchar(500) DEFAULT NULL,
  `trgterIndvdlArray` varchar(500) DEFAULT NULL,
  `svcfrstRegTs` varchar(50) DEFAULT NULL,
  `is_hidden_gem` tinyint(1) DEFAULT 0,
  `updated_at` datetime DEFAULT current_timestamp(),
  `source` varchar(20) DEFAULT 'central',
  `ctpvNm` varchar(50) DEFAULT NULL,
  `sggNm` varchar(50) DEFAULT NULL,
  `enfcBgngYmd` varchar(20) DEFAULT NULL,
  `enfcEndYmd` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`servId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password` varchar(200) NOT NULL,
  `role` int(11) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `region` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS=1;
