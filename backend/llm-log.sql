-- MySQL dump 10.13  Distrib 9.3.0, for Win64 (x86_64)
--
-- Host: localhost    Database: llm-log
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `conversation`
--

DROP TABLE IF EXISTS `conversation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversation` (
  `ConversationId` int NOT NULL AUTO_INCREMENT,
  `LogId` int NOT NULL,
  PRIMARY KEY (`ConversationId`),
  KEY `LogId` (`LogId`),
  CONSTRAINT `conversation_ibfk_1` FOREIGN KEY (`LogId`) REFERENCES `logs` (`LogId`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `conversation`
--

LOCK TABLES `conversation` WRITE;
/*!40000 ALTER TABLE `conversation` DISABLE KEYS */;
INSERT INTO `conversation` VALUES (1,1),(4,1),(5,1),(3,3),(2,4);
/*!40000 ALTER TABLE `conversation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `knowledgebase`
--

DROP TABLE IF EXISTS `knowledgebase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `knowledgebase` (
  `KnowledgeId` int NOT NULL AUTO_INCREMENT,
  `Content` text NOT NULL,
  `ContentType` varchar(255) NOT NULL,
  `MachineId` int NOT NULL,
  `Solution` text,
  PRIMARY KEY (`KnowledgeId`),
  KEY `MachineId` (`MachineId`),
  CONSTRAINT `knowledgebase_ibfk_1` FOREIGN KEY (`MachineId`) REFERENCES `machine` (`MachineId`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `knowledgebase`
--

LOCK TABLES `knowledgebase` WRITE;
/*!40000 ALTER TABLE `knowledgebase` DISABLE KEYS */;
INSERT INTO `knowledgebase` VALUES (1,'Disk space management guide','Document',1,'Replace the cooling system'),(2,'High temperature troubleshooting','Document',1,'Check cooling system or reduce processing load.'),(3,'System reboot steps','Guide',2,'Follow the proper reboot procedure to ensure stability.'),(4,'Network troubleshooting','Guide',3,'Ensure proper cabling and check the network device.'),(5,'Info logs: General guidelines','Info',3,NULL),(6,'High CPU temperature','Warning',1,'Check the cooling system and reduce load'),(7,'High CPU temperature','Warning',1,'Check the cooling system and reduce load'),(8,'High CPU temperature','Warning',1,'Check the cooling system and reduce load');
/*!40000 ALTER TABLE `knowledgebase` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logs`
--

DROP TABLE IF EXISTS `logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `logs` (
  `LogId` int NOT NULL AUTO_INCREMENT,
  `MachineId` int NOT NULL,
  `DateCreated` datetime NOT NULL,
  `LogContent` text NOT NULL,
  PRIMARY KEY (`LogId`),
  KEY `MachineId` (`MachineId`),
  CONSTRAINT `logs_ibfk_1` FOREIGN KEY (`MachineId`) REFERENCES `machine` (`MachineId`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs`
--

LOCK TABLES `logs` WRITE;
/*!40000 ALTER TABLE `logs` DISABLE KEYS */;
INSERT INTO `logs` VALUES (1,1,'2023-10-01 10:00:00','Error: Disk space running low.'),(2,1,'2023-10-01 11:00:00','Warning: High temperature detected.'),(3,2,'2023-10-01 12:00:00','Info: System rebooted successfully.'),(4,3,'2023-10-01 13:00:00','Critical: Network connection lost.'),(5,3,'2023-10-01 14:00:00','Info: Network connection restored.');
/*!40000 ALTER TABLE `logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `machine`
--

DROP TABLE IF EXISTS `machine`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `machine` (
  `MachineId` int NOT NULL AUTO_INCREMENT,
  `MachineName` varchar(255) NOT NULL,
  PRIMARY KEY (`MachineId`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `machine`
--

LOCK TABLES `machine` WRITE;
/*!40000 ALTER TABLE `machine` DISABLE KEYS */;
INSERT INTO `machine` VALUES (1,'Machine A'),(2,'Machine B'),(3,'Machine C');
/*!40000 ALTER TABLE `machine` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `MessageId` int NOT NULL AUTO_INCREMENT,
  `SentDate` datetime NOT NULL,
  `Role` int NOT NULL,
  `Content` text NOT NULL,
  `ConversationId` int NOT NULL,
  PRIMARY KEY (`MessageId`),
  KEY `ConversationId` (`ConversationId`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`ConversationId`) REFERENCES `conversation` (`ConversationId`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES (1,'2023-10-01 15:00:00',1,'What does \"Disk space running low\" mean?',1),(2,'2023-10-01 15:01:00',0,'It means your disk space is almost full. Consider cleaning unnecessary files.',1),(3,'2023-10-01 15:10:00',1,'How do I resolve network connection lost?',2),(4,'2023-10-01 15:11:00',0,'Check your network cables and ensure your router is working correctly.',2),(5,'2023-10-01 15:20:00',1,'What does \"System rebooted successfully\" mean?',3),(6,'2023-10-01 15:21:00',0,'It means the machine was restarted without any errors.',3),(7,'2023-10-01 11:00:00',1,'Another question about the error.',1),(8,'2023-10-01 11:01:00',0,'Please provide more details.',1),(9,'2023-10-01 10:00:00',1,'What does this error mean?',4),(10,'2023-10-01 10:01:00',0,'Disk space is running low.',4),(11,'2023-10-01 11:00:00',1,'Another question about the error.',1),(12,'2023-10-01 11:01:00',0,'Please provide more details.',1),(13,'2023-10-01 10:00:00',1,'What does this error mean?',5),(14,'2023-10-01 10:01:00',0,'Disk space is running low.',5),(15,'2023-10-01 11:00:00',1,'Another question about the error.',1),(16,'2023-10-01 11:01:00',0,'Please provide more details.',1);
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `processedlog`
--

DROP TABLE IF EXISTS `processedlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `processedlog` (
  `ProcessId` int NOT NULL AUTO_INCREMENT,
  `LogId` int NOT NULL,
  `Sentiment` int NOT NULL,
  `Resolved` tinyint(1) NOT NULL,
  PRIMARY KEY (`ProcessId`),
  KEY `LogId` (`LogId`),
  CONSTRAINT `processedlog_ibfk_1` FOREIGN KEY (`LogId`) REFERENCES `logs` (`LogId`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `processedlog`
--

LOCK TABLES `processedlog` WRITE;
/*!40000 ALTER TABLE `processedlog` DISABLE KEYS */;
INSERT INTO `processedlog` VALUES (1,1,-1,1),(2,2,-1,0),(3,3,1,1),(4,4,-1,0),(5,5,1,1);
/*!40000 ALTER TABLE `processedlog` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-03 14:45:07
