<?php

namespace ThoughtBundle\Controller;


use Application\Sonata\UserBundle\Entity\User;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\Routing\Annotation\Route;

class UserProfileController extends Controller
{
    /**
     * @Route("/userprofile/{userId}", name="throught_profile")
     */
    public function showAction($userId)
    {
        $entityManager = $this->container->get('doctrine.orm.entity_manager');
        $user = $entityManager->getRepository(User::class)->find($userId);

//        dump($user); die;
        return $this->render('@ApplicationSonataUser/Thought/userProfile.html.twig', [
            'user'    =>  $user
        ]);
    }
}
