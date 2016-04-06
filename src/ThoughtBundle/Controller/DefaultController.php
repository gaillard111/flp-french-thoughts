<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;

/**
 * Class DefaultController
 * @package ThoughtBundle\Controller
 */
class DefaultController extends Controller
{
    /**
     * @Route("/")
     */
    public function indexAction()
    {
        $parseService = $this->container->get('thought.parser.service')->testParse();

        return $this->render('ThoughtBundle:Default:index.html.twig');
    }
}
