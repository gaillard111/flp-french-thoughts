<?php

namespace Application\Migrations;

use Doctrine\DBAL\Migrations\AbstractMigration;
use Doctrine\DBAL\Schema\Schema;

/**
 * Auto-generated Migration: Please modify to your needs!
 */
class Version20180904135501 extends AbstractMigration
{
    /**
     * @param Schema $schema
     * @throws \Doctrine\DBAL\Migrations\AbortMigrationException
     */
    public function up(Schema $schema)
    {
        // this up() migration is auto-generated, please modify it to your needs
        $this->abortIf($this->connection->getDatabasePlatform()->getName() != 'mysql', 'Migration can only be executed safely on \'mysql\'.');

        $this->addSql('CREATE TABLE dialogs (id INT AUTO_INCREMENT NOT NULL, PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE dialog_user (dialog_id INT NOT NULL, user_id INT NOT NULL, INDEX IDX_14BF095E5E46C4E2 (dialog_id), INDEX IDX_14BF095EA76ED395 (user_id), PRIMARY KEY(dialog_id, user_id)) DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE user_dialog (user_id INT NOT NULL, dialog_id INT NOT NULL, INDEX IDX_2033C35FA76ED395 (user_id), INDEX IDX_2033C35F5E46C4E2 (dialog_id), PRIMARY KEY(user_id, dialog_id)) DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE messages (id INT AUTO_INCREMENT NOT NULL, dialog_id INT DEFAULT NULL, sender_id INT DEFAULT NULL, message_text LONGTEXT NOT NULL, created_at DATETIME NOT NULL, is_viewed TINYINT(1) DEFAULT NULL, INDEX IDX_DB021E965E46C4E2 (dialog_id), INDEX IDX_DB021E96F624B39D (sender_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE friendship (id INT AUTO_INCREMENT NOT NULL, user_id INT DEFAULT NULL, friend_id INT DEFAULT NULL, accepted TINYINT(1) NOT NULL, INDEX IDX_7234A45FA76ED395 (user_id), INDEX IDX_7234A45F6A5458E8 (friend_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE general_mail (id INT AUTO_INCREMENT NOT NULL, subject VARCHAR(255) NOT NULL, body LONGTEXT NOT NULL, is_sended TINYINT(1) NOT NULL, PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ENGINE = InnoDB');
        $this->addSql('ALTER TABLE dialog_user ADD CONSTRAINT FK_14BF095E5E46C4E2 FOREIGN KEY (dialog_id) REFERENCES dialogs (id) ON DELETE CASCADE');
        $this->addSql('ALTER TABLE dialog_user ADD CONSTRAINT FK_14BF095EA76ED395 FOREIGN KEY (user_id) REFERENCES fos_user_user (id) ON DELETE CASCADE');
        $this->addSql('ALTER TABLE user_dialog ADD CONSTRAINT FK_2033C35FA76ED395 FOREIGN KEY (user_id) REFERENCES fos_user_user (id) ON DELETE CASCADE');
        $this->addSql('ALTER TABLE user_dialog ADD CONSTRAINT FK_2033C35F5E46C4E2 FOREIGN KEY (dialog_id) REFERENCES dialogs (id) ON DELETE CASCADE');
        $this->addSql('ALTER TABLE messages ADD CONSTRAINT FK_DB021E965E46C4E2 FOREIGN KEY (dialog_id) REFERENCES dialogs (id)');
        $this->addSql('ALTER TABLE messages ADD CONSTRAINT FK_DB021E96F624B39D FOREIGN KEY (sender_id) REFERENCES fos_user_user (id)');
        $this->addSql('ALTER TABLE friendship ADD CONSTRAINT FK_7234A45FA76ED395 FOREIGN KEY (user_id) REFERENCES fos_user_user (id)');
        $this->addSql('ALTER TABLE friendship ADD CONSTRAINT FK_7234A45F6A5458E8 FOREIGN KEY (friend_id) REFERENCES fos_user_user (id)');
        $this->addSql('ALTER TABLE fos_user_user ADD about LONGTEXT DEFAULT NULL, ADD country VARCHAR(255) DEFAULT NULL, ADD interests LONGTEXT DEFAULT NULL');
        $this->addSql('ALTER TABLE thought_chain ADD user_id INT DEFAULT NULL');
        $this->addSql('ALTER TABLE thought_chain ADD CONSTRAINT FK_21F890EAA76ED395 FOREIGN KEY (user_id) REFERENCES fos_user_user (id)');
        $this->addSql('CREATE INDEX IDX_21F890EAA76ED395 ON thought_chain (user_id)');
        $this->addSql('ALTER TABLE chain ADD is_collective TINYINT(1) NOT NULL, ADD favorite TINYINT(1) NOT NULL');
    }

    /**
     * @param Schema $schema
     * @throws \Doctrine\DBAL\Migrations\AbortMigrationException
     */
    public function down(Schema $schema)
    {
        // this down() migration is auto-generated, please modify it to your needs
        $this->abortIf($this->connection->getDatabasePlatform()->getName() != 'mysql', 'Migration can only be executed safely on \'mysql\'.');

        $this->addSql('ALTER TABLE dialog_user DROP FOREIGN KEY FK_14BF095E5E46C4E2');
        $this->addSql('ALTER TABLE user_dialog DROP FOREIGN KEY FK_2033C35F5E46C4E2');
        $this->addSql('ALTER TABLE messages DROP FOREIGN KEY FK_DB021E965E46C4E2');
        $this->addSql('DROP TABLE dialogs');
        $this->addSql('DROP TABLE dialog_user');
        $this->addSql('DROP TABLE user_dialog');
        $this->addSql('DROP TABLE messages');
        $this->addSql('DROP TABLE friendship');
        $this->addSql('DROP TABLE general_mail');
        $this->addSql('ALTER TABLE chain DROP is_collective, DROP favorite');
        $this->addSql('ALTER TABLE fos_user_user DROP about, DROP country, DROP interests');
        $this->addSql('ALTER TABLE thought_chain DROP FOREIGN KEY FK_21F890EAA76ED395');
        $this->addSql('DROP INDEX IDX_21F890EAA76ED395 ON thought_chain');
        $this->addSql('ALTER TABLE thought_chain DROP user_id');
    }
}
