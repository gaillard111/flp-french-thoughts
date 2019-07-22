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
        $recommendedThoughtService = $this->get('thought.recommended_thought');

        $recommendedThought = $recommendedThoughtService->getThought($this->getUser());

        dump($this->getUser()->getId(), $recommendedThought); die;
    }
}
