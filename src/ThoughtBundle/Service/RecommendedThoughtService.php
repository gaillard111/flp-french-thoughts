<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 19.07.19
 * Time: 14:39
 */

namespace ThoughtBundle\Service;


use Doctrine\ORM\EntityManagerInterface;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\WatchedThought;

class RecommendedThoughtService
{
    /**
     * @var EntityManagerInterface
     */
    private $entityManager;

    public function __construct(EntityManagerInterface $entityManager)
    {
        $this->entityManager = $entityManager;
    }

    public function getThought($user)
    {
        $userWatchedThoughtsData = $this->entityManager->getRepository(Thought::class)->getWatchedStatistics($user);
        $tags = $this->getTags($userWatchedThoughtsData);
        $tagsCount = array_count_values($tags);
        arsort($tagsCount);

        return $this->entityManager->getRepository(Thought::class)->getUnseenUserThoughts($user, $tagsCount);
    }

    public function addWatchedThought($user, $recommendedThought)
    {
        $watchedThought = $this->entityManager->getRepository(WatchedThought::class)->findOneBy(['thought' => $recommendedThought]);

        if (!$watchedThought) {
            $watchedThought = new WatchedThought();
            $watchedThought->setThought($recommendedThought);
            $watchedThought->setUser($user);
            $this->entityManager->persist($watchedThought);
            $this->entityManager->flush();
        }
    }

    private function getTags($userWatchedThoughtsData)
    {
        $tags = [];
        /** @var WatchedThought $thoughtData */
        foreach ($userWatchedThoughtsData as $thoughtData) {
            $thoughtTags = explode(',', $thoughtData['tags']);
            foreach ($thoughtTags as $tag) {
                $tag = trim($tag);
                if ($tag) {
                    $tags[] = $tag;
                }
            }
        }

        return $tags;
    }
}