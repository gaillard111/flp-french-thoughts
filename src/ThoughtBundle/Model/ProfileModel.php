<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use DateTime;
use Doctrine\ORM\EntityManager;
use Exception;
use ThoughtBundle\Entity\PersonalDataRequest;
use ThoughtBundle\Service\Mail;

class ProfileModel
{
    private $em;

    /** @var Mail */
    private $mailService;

    public function __construct(EntityManager $em, Mail $mailService)
    {
        $this->em = $em;
        $this->mailService = $mailService;
    }

    public function requestPersonalData(User $user)
    {
        $repository = $this->em->getRepository(PersonalDataRequest::class);
        $repository->deleteOutDateRequests();
        $request = $repository->getNewRequests($user);

        if ($request) {
            throw new Exception('Request already exist');
        }

        $personalDataRequest = new PersonalDataRequest();
        $personalDataRequest
            ->setUser($user)
            ->setCreatedAt(new DateTime('now'));

        $this->mailService->requestPersonalMail($user);

        $this->em->persist($personalDataRequest);
        $this->em->flush();
    }

    public function removeAccount(User $user)
    {
        $this->em->remove($user);
        $this->em->flush();
    }
}