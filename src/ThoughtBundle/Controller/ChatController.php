<?php

namespace ThoughtBundle\Controller;

use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;

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
