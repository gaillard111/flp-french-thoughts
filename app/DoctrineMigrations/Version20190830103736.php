<?php

namespace Application\Migrations;

use Doctrine\DBAL\Migrations\AbstractMigration;
use Doctrine\DBAL\Schema\Schema;

/**
 * Auto-generated Migration: Please modify to your needs!
 */
class Version20190830103736 extends AbstractMigration
{
    /**
     * @param Schema $schema
     */
    public function up(Schema $schema)
    {
        // this up() migration is auto-generated, please modify it to your needs
        $likes = $this->connection->executeQuery('SELECT id, liked FROM thought WHERE liked > 0')->fetchAll();
        foreach ($likes as $like) {
//            dump($like);die;
            for ($i = 0; $i <= $like['liked']; $i++) {
                $this->addSql('INSERT INTO likes (thought_id) VALUES ('. $like['id'] .')');
            }

        }
//        dump($likesCount); die;
    }

    /**
     * @param Schema $schema
     */
    public function down(Schema $schema)
    {
        // this down() migration is auto-generated, please modify it to your needs

    }
}
