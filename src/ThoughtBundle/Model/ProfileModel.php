<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;

class ProfileModel
{
    protected $em;

    public function __construct(EntityManager $em)
    {
        $this->em = $em;
    }

    public function removeAccount(User $user)
    {
        $this->em->remove($user);
        $this->em->flush();
    }
}