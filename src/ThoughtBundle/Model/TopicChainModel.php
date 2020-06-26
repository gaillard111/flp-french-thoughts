<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use Symfony\Component\Security\Core\Authorization\AuthorizationCheckerInterface;
use ThoughtBundle\Entity\Topic;

class TopicChainModel
{
    private $entityManager;
    private $authorizationChecker;

    public function __construct(EntityManager $entityManager, AuthorizationCheckerInterface $authorizationChecker)
    {
        $this->entityManager = $entityManager;
        $this->authorizationChecker = $authorizationChecker;
    }

    public function getTopicsWithChains() {

        $role = User::ROLE_USER;

        if ($this->authorizationChecker->isGranted(User::ROLE_STUDENT)) {
            $role = User::ROLE_STUDENT;
        }

        $topics = $this->entityManager->getRepository(Topic::class)->searchTopics($role);

        $topicsArray = [];
        foreach ($topics as $topic) {

            $chainArray = [];

            foreach ($topic->getChains() as $chain) {
                $chainArray[] = [
                    $chain->getId(),
                    $chain->getName(),
                ];
            }

            usort($chainArray, function($a, $b){
                return ($a[1] > $b[1]);
            });

            $topicsArray[] = [
                'topic_id' => $topic->getId(),
                'topic_name' => $topic->getName(),
                'topic_chains' => $topic->getChains()->toArray()
            ];
        }
        return $topicsArray;
    }

    public function getUserPrivateChaines(User $user) {
        $arrayChaines = [];
        foreach ($user->getChains() as $userChain) {
            if ($userChain->getIsPrivate()) {
                $arrayChaines[] = $userChain;
            }
        }

        return [
            'topic_id' => 0,
            'topic_name' => 'Private',
            'topic_chains' => $arrayChaines
        ];
    }

}