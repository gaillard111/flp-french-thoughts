<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Application\Sonata\UserBundle\Entity\Message;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\SubmitType;
use Symfony\Component\Form\Extension\Core\Type\TextareaType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;

class MessageType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('messageText', TextareaType::class, [
                'attr'      =>  [
                        'class' =>  'form-control'
                ],
                'label'     =>  'user.dialogs.message_text',
                'required'  => false,
            ])
            ->add('submit', SubmitType::class, [
                'attr'      =>  [
                        'class' =>  'btn btn-info pull-right'
                ],
                'label'     =>  'user.dialogs.message_submit',
            ]);
    }

    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class'    => Message::class,
        ]);
    }

    public function getBlockPrefix()
    {
        return 'application_sonata_user_bundle_message_type';
    }
}
