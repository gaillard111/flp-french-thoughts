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

        $userWatchedThoughts = $em->getRepository(Thought::class)->getUnseenUserThoughts($this->getUser());

        dump($this->getUser()->getId(), $userWatchedThoughts); die;
    }
}
