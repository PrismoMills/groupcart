-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: ecommerceplatform
-- ------------------------------------------------------
-- Server version	8.0.41
CREATE DATABASE ecommerceplatform;
USE ecommerceplatform;

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
-- Table structure for table `customer`
--

DROP TABLE IF EXISTS `customer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer` (
  `CustomerID` varchar(50) NOT NULL COMMENT 'Unique customer identifier',
  `ContactNumber` varchar(20) NOT NULL COMMENT 'Primary contact number',
  `ShippingDetails` text NOT NULL COMMENT 'Default shipping address',
  `password` varchar(255) NOT NULL COMMENT 'Plaintext password (for testing purposes only)',
  PRIMARY KEY (`CustomerID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer`
--

LOCK TABLES `customer` WRITE;
/*!40000 ALTER TABLE `customer` DISABLE KEYS */;
INSERT INTO `customer` VALUES ('C001','+1-555-0101','123 Main St, San Francisco, CA 94105','C001'),('C002','+44-20-7946-0123','456 Oxford St, London W1A 1AB','C002'),('C003','+61-2-9876-5432','789 George St, Sydney NSW 2000','C003'),('C004','+33-1-2345-6789','101 Rue de Rivoli, Paris 75001','C004'),('C005','+1-555-0202','202 Central Park West, New York, NY 10023','C005'),('C006','+49-30-901820','Alexanderplatz 1, 10178 Berlin, Germany','C006'),('C007','+1-416-555-0199','220 Yonge St, Toronto, ON M5B 2H1','C007'),('C008','+41-22-909-7000','Rue du Rhône 120, 1204 Geneva, Switzerland','C008'),('C009','+61-3-9663-4321','Flinders St, Melbourne VIC 3000','C009'),('C010','+1-312-555-0123','600 W Chicago Ave, Chicago, IL 60654','C010');
/*!40000 ALTER TABLE `customer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product`
--

DROP TABLE IF EXISTS `product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product` (
  `ProductID` varchar(50) NOT NULL COMMENT 'Unique product identifier',
  `VendorID` varchar(50) NOT NULL COMMENT 'References Vendor(VendorID)',
  `Name` varchar(100) NOT NULL COMMENT 'Product name',
  `ListedPrice` decimal(10,2) NOT NULL COMMENT 'Current listed price',
  PRIMARY KEY (`ProductID`),
  KEY `VendorID` (`VendorID`),
  CONSTRAINT `product_ibfk_1` FOREIGN KEY (`VendorID`) REFERENCES `vendor` (`VendorID`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product`
--

LOCK TABLES `product` WRITE;
/*!40000 ALTER TABLE `product` DISABLE KEYS */;
INSERT INTO `product` VALUES ('P10001','V010','200-Piece Tool Kit with Case',149.75),('P10002','V010','Cordless Drill & Driver Kit',129.99),('P1001','V001','Wireless Bluetooth Headphones',199.99),('P1002','V001','Smartwatch Pro',299.50),('P1003','V001','4K Action Camera',450.00),('P1004','V001','Noise-Canceling Wireless Earbuds',179.99),('P1005','V001','8K Professional Drone',1299.00),('P2001','V002','Organic Almonds (1kg)',12.99),('P2002','V002','Cold-Pressed Olive Oil',24.50),('P2003','V002','Organic Quinoa (1kg)',8.99),('P2004','V002','Pure Maple Syrup (500ml)',15.75),('P3001','V003','Camping Tent (4-person)',189.00),('P3002','V003','Hiking Backpack 60L',145.75),('P3003','V003','Ultralight Sleeping Bag (-10°C)',210.00),('P3004','V003','Telescoping Fishing Rod',89.95),('P4001','V004','Designer Sunglasses',89.95),('P4002','V004','Leather Handbag',220.00),('P4003','V004','Cashmere Scarf',149.00),('P4004','V004','Stainless Steel Chronograph Watch',399.00),('P5001','V005','The Great Novel (Hardcover)',29.99),('P5002','V005','Cooking Masterclass Recipe Book',45.00),('P5003','V005','AI & Machine Learning Essentials',89.50),('P5004','V005','World Atlas Deluxe Edition',65.00),('P6001','V006','Reusable Silicone Food Bags (Set of 10)',24.99),('P6002','V006','Bamboo Toothbrush (4-pack)',12.50),('P6003','V006','Solar-Powered Garden Lights (6-pack)',45.00),('P6004','V006','Compostable Party Plates (50 units)',18.99),('P7001','V007','Adjustable Dumbbell Set (50kg)',299.00),('P7002','V007','Yoga Mat with Alignment Lines',45.95),('P8001','V008','Automatic Skeleton Watch',2499.00),('P8002','V008','Diamond-Studded Dress Watch',5899.00),('P9001','V009','Self-Cleaning Cat Litter Box',199.00),('P9002','V009','GPS Pet Tracker Collar',89.95);
/*!40000 ALTER TABLE `product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producttag`
--

DROP TABLE IF EXISTS `producttag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producttag` (
  `ProductID` varchar(50) NOT NULL COMMENT 'References Product(ProductID)',
  `TagID` int NOT NULL COMMENT 'References Tag(TagID)',
  PRIMARY KEY (`ProductID`,`TagID`),
  KEY `TagID` (`TagID`),
  CONSTRAINT `producttag_ibfk_1` FOREIGN KEY (`ProductID`) REFERENCES `product` (`ProductID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `producttag_ibfk_2` FOREIGN KEY (`TagID`) REFERENCES `tag` (`TagID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producttag`
--

LOCK TABLES `producttag` WRITE;
/*!40000 ALTER TABLE `producttag` DISABLE KEYS */;
INSERT INTO `producttag` VALUES ('P1001',1),('P1002',1),('P1003',1),('P1004',1),('P1005',1),('P6002',1),('P1001',2),('P1003',2),('P1004',2),('P7002',2),('P9002',2),('P2001',3),('P2002',3),('P2003',3),('P2004',3),('P6001',3),('P3001',4),('P3002',4),('P3003',4),('P3004',4),('P4001',5),('P4002',5),('P4003',5),('P4004',5),('P1002',6),('P2001',6),('P2004',6),('P4004',6),('P5001',6),('P5002',6),('P5003',6),('P3001',7),('P5002',7),('P10002',8),('P1001',8),('P1004',8),('P4001',8),('P5003',8),('P3003',9),('P6001',9),('P6002',9),('P6003',9),('P6004',9),('P6003',10),('P9001',10),('P7001',11),('P7002',11),('P4003',12),('P8001',12),('P8002',12),('P9001',13),('P9002',13),('P10001',14),('P10002',14),('P1005',16),('P5004',16),('P8001',16);
/*!40000 ALTER TABLE `producttag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tag`
--

DROP TABLE IF EXISTS `tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tag` (
  `TagID` int NOT NULL AUTO_INCREMENT COMMENT 'Unique tag identifier',
  `TagName` varchar(50) NOT NULL COMMENT 'Tag display name',
  PRIMARY KEY (`TagID`),
  UNIQUE KEY `TagName` (`TagName`),
  KEY `idx_tagname` (`TagName`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tag`
--

LOCK TABLES `tag` WRITE;
/*!40000 ALTER TABLE `tag` DISABLE KEYS */;
INSERT INTO `tag` VALUES (6,'Bestseller'),(7,'Discount'),(14,'DIY'),(9,'Eco-Friendly'),(1,'Electronics'),(5,'Fashion'),(11,'Fitness'),(15,'Kids'),(16,'Limited Edition'),(12,'Luxury'),(8,'New Arrival'),(3,'Organic'),(4,'Outdoor'),(13,'Pet Care'),(2,'Portable'),(10,'Smart Home');
/*!40000 ALTER TABLE `tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transaction`
--

DROP TABLE IF EXISTS `transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transaction` (
  `TransactionID` varchar(50) NOT NULL COMMENT 'Unique transaction identifier',
  `CustomerID` varchar(50) NOT NULL COMMENT 'References Customer(CustomerID)',
  `TransactionDate` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Transaction timestamp',
  `TotalAmount` decimal(10,2) DEFAULT NULL COMMENT 'Calculated order total',
  `status` enum('PENDING_SHIPMENT','SHIPPED','COMPLETED','CANCELLED') NOT NULL DEFAULT 'PENDING_SHIPMENT' COMMENT 'Order status: PENDING_SHIPMENT/SHIPPED/COMPLETED/CANCELLED',
  PRIMARY KEY (`TransactionID`),
  KEY `idx_transaction_customer_date` (`CustomerID`,`TransactionDate`),
  CONSTRAINT `transaction_ibfk_1` FOREIGN KEY (`CustomerID`) REFERENCES `customer` (`CustomerID`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transaction`
--

LOCK TABLES `transaction` WRITE;
/*!40000 ALTER TABLE `transaction` DISABLE KEYS */;
INSERT INTO `transaction` VALUES ('T20231001','C001','2023-10-01 14:30:00',389.99,'COMPLETED'),('T20231002','C002','2023-10-02 09:15:00',24.50,'COMPLETED'),('T20231003','C003','2023-10-03 16:45:00',334.75,'COMPLETED'),('T20231004','C004','2023-10-04 11:00:00',220.00,'COMPLETED'),('T20231005','C005','2023-10-05 17:30:00',74.99,'COMPLETED'),('T20231006','C006','2023-10-06 13:20:00',199.00,'COMPLETED'),('T20231007','C007','2023-10-07 10:45:00',344.95,'COMPLETED'),('T20231008','C008','2023-10-08 16:10:00',8398.00,'COMPLETED'),('T20231009','C009','2023-10-09 11:30:00',288.95,'COMPLETED'),('T20231010','C010','2023-10-10 18:00:00',279.74,'COMPLETED'),('T20231011','C001','2023-10-11 15:20:00',658.99,'COMPLETED'),('T20231012','C002','2023-10-12 10:10:00',214.75,'COMPLETED'),('T20231013','C003','2023-10-13 17:45:00',1504.95,'COMPLETED'),('T20231014','C004','2023-10-14 12:30:00',89.95,'COMPLETED'),('T20231015','C005','2023-10-15 19:00:00',184.99,'COMPLETED');
/*!40000 ALTER TABLE `transaction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactionitem`
--

DROP TABLE IF EXISTS `transactionitem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactionitem` (
  `TransactionItemID` int NOT NULL AUTO_INCREMENT COMMENT 'Auto-increment primary key',
  `TransactionID` varchar(50) NOT NULL COMMENT 'References Transaction(TransactionID)',
  `ProductID` varchar(50) NOT NULL COMMENT 'References Product(ProductID)',
  `Quantity` int NOT NULL DEFAULT '1' COMMENT 'Purchased quantity',
  `PriceAtPurchase` decimal(10,2) DEFAULT NULL COMMENT 'Price at transaction time',
  PRIMARY KEY (`TransactionItemID`),
  KEY `idx_transactionitem_product` (`ProductID`),
  KEY `idx_transactionitem_transaction` (`TransactionID`),
  CONSTRAINT `transactionitem_ibfk_1` FOREIGN KEY (`TransactionID`) REFERENCES `transaction` (`TransactionID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `transactionitem_ibfk_2` FOREIGN KEY (`ProductID`) REFERENCES `product` (`ProductID`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactionitem`
--

LOCK TABLES `transactionitem` WRITE;
/*!40000 ALTER TABLE `transactionitem` DISABLE KEYS */;
INSERT INTO `transactionitem` VALUES (1,'T20231001','P1001',1,189.99),(2,'T20231001','P5002',1,40.00),(3,'T20231002','P2002',1,24.50),(4,'T20231003','P3001',1,169.00),(5,'T20231003','P3002',1,145.75),(6,'T20231004','P4002',1,220.00),(7,'T20231005','P5001',1,29.99),(8,'T20231005','P2001',2,12.99),(9,'T20231006','P6001',2,22.99),(10,'T20231006','P2001',3,11.99),(11,'T20231007','P7001',1,279.00),(12,'T20231007','P7002',1,45.95),(13,'T20231008','P8002',1,5899.00),(14,'T20231008','P4001',1,79.95),(15,'T20231008','P1003',1,420.00),(16,'T20231009','P9001',1,189.00),(17,'T20231009','P9002',1,85.00),(18,'T20231009','P3002',1,140.00),(19,'T20231010','P10001',1,139.99),(20,'T20231010','P10002',1,119.99),(21,'T20231010','P5001',2,27.99),(22,'T20231011','P1004',1,179.99),(23,'T20231011','P5003',1,79.99),(24,'T20231011','P6003',2,40.00),(25,'T20231011','P2004',3,14.50),(26,'T20231012','P3003',1,199.00),(27,'T20231012','P2003',2,8.50),(28,'T20231013','P8001',1,2299.00),(29,'T20231013','P4004',1,379.00),(30,'T20231013','P1005',1,1199.00),(31,'T20231014','P4003',1,139.00),(32,'T20231015','P6004',5,17.99),(33,'T20231015','P5004',1,59.99);
/*!40000 ALTER TABLE `transactionitem` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `UpdateTotalAmountAfterInsert` AFTER INSERT ON `transactionitem` FOR EACH ROW BEGIN
  UPDATE Transaction t
  SET t.TotalAmount = (
    SELECT SUM(Quantity * PriceAtPurchase)
    FROM TransactionItem ti
    WHERE ti.TransactionID = NEW.TransactionID
  )
  WHERE t.TransactionID = NEW.TransactionID;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `UpdateTotalAmountAfterUpdate` AFTER UPDATE ON `transactionitem` FOR EACH ROW BEGIN
  UPDATE Transaction t
  SET t.TotalAmount = (
    SELECT SUM(Quantity * PriceAtPurchase)
    FROM TransactionItem ti
    WHERE ti.TransactionID = NEW.TransactionID
  )
  WHERE t.TransactionID = NEW.TransactionID;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `UpdateTotalAmountAfterDelete` AFTER DELETE ON `transactionitem` FOR EACH ROW BEGIN
  UPDATE Transaction t
  SET t.TotalAmount = (
    SELECT SUM(Quantity * PriceAtPurchase)
    FROM TransactionItem ti
    WHERE ti.TransactionID = OLD.TransactionID
  )
  WHERE t.TransactionID = OLD.TransactionID;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `vendor`
--

DROP TABLE IF EXISTS `vendor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vendor` (
  `VendorID` varchar(50) NOT NULL COMMENT 'Unique vendor identifier',
  `BusinessName` varchar(100) NOT NULL COMMENT 'Legal business name',
  `CustomerFeedbackScore` decimal(3,2) DEFAULT NULL COMMENT 'Customer rating (0-5 scale)',
  `GeographicalPresence` varchar(100) DEFAULT NULL COMMENT 'Geographic operation areas',
  `password` varchar(255) NOT NULL COMMENT 'Plaintext password (for testing purposes only)',
  PRIMARY KEY (`VendorID`),
  CONSTRAINT `vendor_chk_1` CHECK ((`CustomerFeedbackScore` between 0 and 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vendor`
--

LOCK TABLES `vendor` WRITE;
/*!40000 ALTER TABLE `vendor` DISABLE KEYS */;
INSERT INTO `vendor` VALUES ('V001','TechGadgets Inc.',4.70,'San Francisco, USA','V001'),('V002','FreshFoods Ltd.',4.50,'London, UK','V002'),('V003','OutdoorAdventures',4.20,'Sydney, Australia','V003'),('V004','FashionHub',4.80,'Paris, France','V004'),('V005','BookWorld',4.60,'New York, USA','V005'),('V006','GreenHome Essentials',4.40,'Berlin, Germany','V006'),('V007','SportsGear Pro',4.30,'Toronto, Canada','V007'),('V008','LuxuryWatches Co.',4.90,'Geneva, Switzerland','V008'),('V009','PetParadise',4.60,'Melbourne, Australia','V009'),('V010','DIYWorkshop',4.20,'Chicago, USA','V010');
/*!40000 ALTER TABLE `vendor` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-07  9:54:20
