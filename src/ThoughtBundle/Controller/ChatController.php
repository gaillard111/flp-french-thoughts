<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;

class ChatController extends Controller
{
    /**
     * @Route("/discuter", methods={"GET"}, options={"sitemap" = true})
     */
    public function indexAction()
    {
        return $this->render('chat.html.twig');
    }
}
