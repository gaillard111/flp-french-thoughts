<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\WatchedThought;

class RecommendedThoughtController extends Controller
{
    /**
     * @Route("/recommended", name="recommended_thoughts")
     */
    public function indexAction()
    {
        $em = $this->get('doctrine.orm.entity_manager');


        $userWatchedThoughtsData = $em->getRepository(Thought::class)->getWatchedStatistics($this->getUser());

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





        $tagsCount = array_count_values($tags);

//        dump($tagsCount);
        arsort($tagsCount);

//        dump($tagsCount);die;
        $userUnseenThoughts = $em->getRepository(Thought::class)->getUnseenUserThoughts($this->getUser(), $tagsCount);
//        foreach ($tagsCount as $tag => $count) {
//
//        }


        dump($this->getUser()->getId(), $userUnseenThoughts, $tags); die;
    }
}
