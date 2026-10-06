-- =============================================================================
--  BazarNimal - Base de datos MySQL 8
-- =============================================================================
--  Ejecutar UNA sola vez con un usuario administrador de MySQL (root), usando
--  el script scripts/setup_database.ps1 desde la carpeta Backend.
--
--  IMPORTANTE: no escribas barras invertidas en este archivo (ni en comentarios):
--  el cliente mysql las interpreta como comandos.
--
--  1. Las contraseñas de los usuarios de MySQL NO están en este archivo: el
--     script las toma de DB_PASSWORD y DB_MIGRATION_PASSWORD del .env y las
--     define como @app_password / @migrator_password antes de ejecutarlo.
--     Si no vienen definidas (o tienen menos de 16 caracteres) el archivo se
--     detiene sin crear usuarios.
--  2. El esquema (sección 3) es el mismo que genera la migración
--     src/core/database/migrations/versions/0001_initial_schema.py y queda
--     marcado en alembic_version, así que al arrancar el backend no lo vuelve
--     a crear. Los cambios futuros se hacen con migraciones nuevas, que el
--     backend ejecuta automáticamente al iniciar.
--  3. El administrador inicial NO se inserta aquí: el backend lo crea al
--     arrancar con ADMIN_NAME / ADMIN_EMAIL / ADMIN_PASSWORD del .env, porque
--     el correo va cifrado (AES-256-GCM) y la contraseña con Argon2id.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Base de datos y verificación de contraseñas
-- -----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS bazarnimal
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

DROP PROCEDURE IF EXISTS bazarnimal.check_setup_passwords;
DELIMITER //
CREATE PROCEDURE bazarnimal.check_setup_passwords()
BEGIN
    IF @app_password IS NULL OR CHAR_LENGTH(@app_password) < 16
       OR @migrator_password IS NULL OR CHAR_LENGTH(@migrator_password) < 16 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Faltan @app_password/@migrator_password (16+ caracteres). Usa scripts/setup_database.ps1';
    END IF;
END //
DELIMITER ;
CALL bazarnimal.check_setup_passwords();
DROP PROCEDURE bazarnimal.check_setup_passwords;


-- -----------------------------------------------------------------------------
-- 2. Usuarios con privilegios mínimos
-- -----------------------------------------------------------------------------

-- Usuario de la aplicación: solo lee, inserta y actualiza (los borrados son lógicos).
-- Sin DROP, sin ALTER, sin GRANT y sin acceso a otras bases.
SET @sql = CONCAT('CREATE USER IF NOT EXISTS `bazarnimal_app`@`localhost` IDENTIFIED BY ', QUOTE(@app_password));
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
SET @sql = CONCAT('CREATE USER IF NOT EXISTS `bazarnimal_app`@`127.0.0.1` IDENTIFIED BY ', QUOTE(@app_password));
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
GRANT SELECT, INSERT, UPDATE ON bazarnimal.* TO 'bazarnimal_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON bazarnimal.* TO 'bazarnimal_app'@'127.0.0.1';

-- Usuario de migraciones: puede crear y modificar tablas, solo en esta base.
SET @sql = CONCAT('CREATE USER IF NOT EXISTS `bazarnimal_migrator`@`localhost` IDENTIFIED BY ', QUOTE(@migrator_password));
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
SET @sql = CONCAT('CREATE USER IF NOT EXISTS `bazarnimal_migrator`@`127.0.0.1` IDENTIFIED BY ', QUOTE(@migrator_password));
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
GRANT ALL PRIVILEGES ON bazarnimal.* TO 'bazarnimal_migrator'@'localhost';
GRANT ALL PRIVILEGES ON bazarnimal.* TO 'bazarnimal_migrator'@'127.0.0.1';

FLUSH PRIVILEGES;

SET @app_password = NULL;
SET @migrator_password = NULL;
SET @sql = NULL;


-- -----------------------------------------------------------------------------
-- 3. Esquema (generado desde la migración 0001_initial_schema)
-- -----------------------------------------------------------------------------
USE bazarnimal;
SET time_zone = '+00:00';

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Migración 0001_initial_schema

CREATE TABLE users (
    id CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email_encrypted VARCHAR(512) NOT NULL,
    email_hash CHAR(64) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_encrypted VARCHAR(512),
    `role` ENUM('user','admin') NOT NULL DEFAULT 'user',
    is_active BOOL NOT NULL DEFAULT true,
    failed_login_attempts INTEGER UNSIGNED NOT NULL DEFAULT '0',
    locked_until DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT uq_users_email_hash UNIQUE (email_hash)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_users_role ON users (`role`);

CREATE TABLE refresh_tokens (
    id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    token_hash CHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME,
    replaced_by CHAR(36),
    created_by_ip VARCHAR(45),
    user_agent VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_refresh_tokens_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_refresh_tokens_token_hash UNIQUE (token_hash)
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens (expires_at);

CREATE TABLE pets (
    id CHAR(36) NOT NULL,
    name VARCHAR(80) NOT NULL,
    species ENUM('dog','cat') NOT NULL,
    breed VARCHAR(80) NOT NULL,
    age_years TINYINT UNSIGNED NOT NULL DEFAULT '0',
    age_months TINYINT UNSIGNED NOT NULL DEFAULT '0',
    image_url VARCHAR(255) NOT NULL,
    status ENUM('in_adoption','adopted') NOT NULL DEFAULT 'in_adoption',
    created_by CHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT fk_pets_created_by FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_pets_listing ON pets (deleted_at, status, species);

CREATE INDEX ix_pets_name ON pets (name);

CREATE TABLE adoption_requests (
    id CHAR(36) NOT NULL,
    pet_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    reviewed_by CHAR(36),
    reviewed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT fk_adoption_requests_pet FOREIGN KEY(pet_id) REFERENCES pets (id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_adoption_requests_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_adoption_requests_reviewed_by FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_adoption_requests_status ON adoption_requests (deleted_at, status);

CREATE TABLE products (
    id CHAR(36) NOT NULL,
    name VARCHAR(120) NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    weight_kg NUMERIC(8, 3),
    pieces INTEGER UNSIGNED,
    status ENUM('available','unavailable') NOT NULL DEFAULT 'available',
    created_by CHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT fk_products_created_by FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE RESTRICT ON UPDATE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_products_listing ON products (deleted_at, status);

CREATE INDEX ix_products_name ON products (name);

CREATE TABLE posts (
    id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    reviewed_by CHAR(36),
    reviewed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    PRIMARY KEY (id),
    CONSTRAINT fk_posts_user FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_posts_reviewed_by FOREIGN KEY(reviewed_by) REFERENCES users (id) ON DELETE SET NULL ON UPDATE CASCADE
)ENGINE=InnoDB CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE INDEX ix_posts_listing ON posts (deleted_at, status, created_at);

INSERT INTO alembic_version (version_num) VALUES ('0001_initial_schema');

