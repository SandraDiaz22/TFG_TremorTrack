-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Versión del servidor:         11.4.0-MariaDB - mariadb.org binary distribution
-- SO del servidor:              Win64
-- HeidiSQL Versión:             12.3.0.6589
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Volcando estructura de base de datos para parkinson
CREATE DATABASE IF NOT EXISTS `parkinson` /*!40100 DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci */;
USE `parkinson`;

-- Volcando estructura para tabla parkinson.administrador
CREATE TABLE IF NOT EXISTS `administrador` (
  `id_admin` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_de_usuario` varchar(50) NOT NULL DEFAULT '0',
  `contraseña` varchar(64) NOT NULL DEFAULT '0',
  `correo_electronico` varchar(255) NOT NULL DEFAULT '0',
  `nombre` varchar(50) NOT NULL DEFAULT '0',
  `apellido` varchar(50) NOT NULL DEFAULT '0',
  `foto` varchar(255) DEFAULT '' COMMENT 'ruta de la imagen',
  PRIMARY KEY (`id_admin`),
  UNIQUE KEY `id_admin` (`id_admin`),
  UNIQUE KEY `correo_electronico` (`correo_electronico`),
  UNIQUE KEY `nombre_de_usuario` (`nombre_de_usuario`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci CHECKSUM=1;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla parkinson.medico
CREATE TABLE IF NOT EXISTS `medico` (
  `id_medico` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_de_usuario` varchar(50) NOT NULL DEFAULT '',
  `contraseña` varchar(64) NOT NULL DEFAULT '',
  `correo_electronico` varchar(255) NOT NULL DEFAULT '',
  `nombre` varchar(50) NOT NULL DEFAULT '',
  `apellido` varchar(50) NOT NULL DEFAULT '',
  `foto` varchar(255) DEFAULT '' COMMENT 'ruta de la imagen',
  PRIMARY KEY (`id_medico`) USING BTREE,
  UNIQUE KEY `nombre_de_usuario` (`nombre_de_usuario`),
  UNIQUE KEY `correo_electronico` (`correo_electronico`),
  UNIQUE KEY `id_médico` (`id_medico`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla parkinson.paciente
CREATE TABLE IF NOT EXISTS `paciente` (
  `id_paciente` int(11) NOT NULL AUTO_INCREMENT,
  `nombre_de_usuario` varchar(50) NOT NULL,
  `contraseña` varchar(64) NOT NULL DEFAULT '0',
  `correo_electronico` varchar(255) NOT NULL DEFAULT '0',
  `nombre` varchar(50) NOT NULL DEFAULT '0',
  `apellido` varchar(50) NOT NULL DEFAULT '0',
  `foto` varchar(255) DEFAULT NULL,
  `fecha_de_nacimiento` date NOT NULL,
  `sensor` enum('SI','NO') DEFAULT NULL,
  `direccion` varchar(255) NOT NULL DEFAULT '0',
  `telefono` varchar(15) NOT NULL DEFAULT '0',
  `id_medico` int(11) DEFAULT NULL,
  `lateralidad` enum('diestro','zurdo') DEFAULT NULL,
  PRIMARY KEY (`id_paciente`),
  UNIQUE KEY `id_paciente` (`id_paciente`),
  UNIQUE KEY `nombre de usuario` (`nombre_de_usuario`) USING BTREE,
  UNIQUE KEY `correo_electronico` (`correo_electronico`),
  KEY `FK_Paciente_Médico` (`id_medico`) USING BTREE,
  CONSTRAINT `FK_Paciente_Médico` FOREIGN KEY (`id_medico`) REFERENCES `medico` (`id_medico`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla parkinson.registros
CREATE TABLE IF NOT EXISTS `registros` (
  `id_registro` int(11) NOT NULL AUTO_INCREMENT,
  `paciente` int(11) NOT NULL,
  `datos_en_crudo` varchar(250) NOT NULL DEFAULT '',
  `fecha_inicial` date DEFAULT NULL,
  `fecha_final` date DEFAULT NULL,
  PRIMARY KEY (`id_registro`) USING BTREE,
  KEY `FK_registros_paciente` (`paciente`),
  CONSTRAINT `FK_registros_paciente` FOREIGN KEY (`paciente`) REFERENCES `paciente` (`id_paciente`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=207 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla parkinson.videos
CREATE TABLE IF NOT EXISTS `videos` (
  `id_video` int(11) NOT NULL AUTO_INCREMENT,
  `paciente` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `contenido` varchar(250) NOT NULL DEFAULT '',
  `mano_dominante` enum('derecha','izquierda') NOT NULL,
  `lentitud` enum('0','1','2','3','4') DEFAULT NULL,
  `amplitud` enum('0','1','2','3','4') DEFAULT NULL,
  `velocidad_media` varchar(50) DEFAULT NULL,
  `frecuencia_max` varchar(50) DEFAULT NULL,
  `frecuencia_min` varchar(50) DEFAULT NULL,
  `promedio_max` varchar(50) DEFAULT NULL,
  `desv_estandar_max` varchar(50) DEFAULT NULL,
  `diferencia_ranurada_min` varchar(50) DEFAULT NULL,
  `diferencia_ranurada_max` varchar(50) DEFAULT NULL,
  `caracteristicas` text DEFAULT NULL,
  PRIMARY KEY (`id_video`),
  KEY `FK_Videos_Paciente` (`paciente`),
  CONSTRAINT `FK_Videos_Paciente` FOREIGN KEY (`paciente`) REFERENCES `paciente` (`id_paciente`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=172 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- La exportación de datos fue deseleccionada.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
