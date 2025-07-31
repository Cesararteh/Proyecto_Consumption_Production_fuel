-- Creamos un procedimiento práctico para mostrar los datos 
DELIMITER //
CREATE PROCEDURE shown()
BEGIN
	SELECT * FROM database_fuel LIMIT 10;
END //
DELIMITER ; 

CALL shown();

-- Esta sección es para renombar cada columna, solo si es pertinente.
ALTER TABLE database_fuel 
CHANGE COLUMN `Entity` Country VARCHAR(40) NULL;

-- Esta sección es para crear tablas sin duplicados 
CREATE TABLE Year (
    id_Year INT AUTO_INCREMENT PRIMARY KEY,
    Year INT UNIQUE
);
CREATE TABLE Country (
    id_Country INT AUTO_INCREMENT PRIMARY KEY,
    Country INT UNIQUE
);

-- Part 1: Verificar los datos y crear una tabla con los datos no duplicados
CREATE TABLE table_year AS
SELECT DISTINCT Year AS All_year
FROM database_fuel
ORDER BY all_year;

ALTER TABLE table_year 
ADD COLUMN Id_year INT NOT NULL AUTO_INCREMENT PRIMARY KEY;

CREATE TABLE table_country AS
SELECT DISTINCT Country AS All_country
FROM database_fuel
ORDER BY all_country;

ALTER TABLE table_country 
ADD COLUMN Id_country INT NOT NULL AUTO_INCREMENT PRIMARY KEY;

-- Vamos a verificar si hay valores nulos en cada una de las columnas.alter

SELECT COUNT(*) AS total_nulos
FROM database_fuel
WHERE Gas_production IS NULL;
-- Nota: No hay valores nulos en la base de datos.

-- Verificar los duplicados (Se conoce si hay registros de cada país en cada año)
SELECT Country, COUNT(*) AS Cantidad_duplicados
FROM database_fuel
group by country 
having count(*)>1;

-- Verificar si todos los nombres de los paises no tienen espacios extras

select Country from database_fuel
where length(Country) - length(trim(Country)) > 0; 
-- Todos los paises estan bien escritos

-- Primera mision: Hay paises que no tienen demasiados registros como para realizar regresion
-- Criterio de >=20 años de diferencia para realizar regresion
CREATE TABLE table_country as WITH year_sequence AS (
  SELECT 
    Country,
    Year,
    ROW_NUMBER() OVER (PARTITION BY Country ORDER BY Year) AS rn
  FROM database_fuel
),
gaps AS (
  SELECT 
    Country,
    Year,
    rn,
    Year - rn AS gap_key
  FROM year_sequence
),
grouped_gaps AS (
  SELECT 
    Country,
    COUNT(*) AS streak_length
  FROM gaps
  GROUP BY Country, gap_key
),
final AS (
  SELECT 
    Country,
    MAX(streak_length) AS max_continuous_years
  FROM grouped_gaps
  GROUP BY Country
)
SELECT 
  f.Country,
  CASE 
    WHEN f.max_continuous_years >= 20 THEN 'Habilitado'
    ELSE 'No Habilitado'
  END AS Criterio_regresion
FROM final f;

ALTER TABLE table_country 
ADD COLUMN Id_country INT NOT NULL AUTO_INCREMENT PRIMARY KEY;

-- Vamos a añadir los "id" a la tabla principal
-- Agregar columna si no existe
ALTER TABLE database_fuel ADD COLUMN id_country INT;
ALTER TABLE database_fuel ADD COLUMN id_year INT;
SET SQL_SAFE_UPDATES = 0;

UPDATE database_fuel db
JOIN table_country c ON db.Country = c.Country
SET db.id_country = c.Id_country;

UPDATE database_fuel db
JOIN table_year c ON db.Year = c.All_year
SET db.id_year = c.id_year;

SET SQL_SAFE_UPDATES = 0;

-- Colocar latitud y longitud de la base de datos externa
ALTER TABLE table_country ADD COLUMN latitud INT;
ALTER TABLE table_country ADD COLUMN longitud INT;
UPDATE table_country x
JOIN coordenadas_paises c ON x.Id_Country = c.id_country
SET 
  x.latitud = c.latitude,
  x.longitud = c.longitude;

-- Falta cambiar el tipo de dato para que sea decimal la latitud y longitud 
ALTER TABLE table_country
MODIFY latitud DECIMAL(10,6),
MODIFY longitud DECIMAL(10,6);